#!/bin/env python3 

from asyncio import Protocol, Event, get_running_loop, run
from ssl import create_default_context, Purpose
from urllib.parse import urlparse
from logging import getLogger, DEBUG, INFO, WARN, ERROR
from logging.config import dictConfig
from os.path import exists, join, abspath, normpath
from os import getcwd
from mimetypes import guess_type, add_type

TIMEOUT = 1

dictConfig({
    "version": 1,
    "formatters": {
        "service": {
            "format" : "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(funcName)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class"    : "logging.StreamHandler",
            "formatter": "service",
            "level"    : "INFO",
            "stream"   : "ext://sys.stdout"
        }
    },
    "root": {
        "level"   : "DEBUG",
        "handlers": ["console"]
    }
})

log = getLogger(__name__)

class GeminiProtocol(Protocol):
    def __init__(self):
        # Enable flow control
        self._can_write = Event()
        self._can_write.set()
        # Enable timeouts
        loop = get_running_loop()
        self.timeout_handle = loop.call_later(TIMEOUT, self._timeout)
        log.debug(f"Timeout: {TIMEOUT}s")
        
    def pause_writing(self) -> None:
        log.debug("Pausing data transfer")
        self._can_write.clear()

    def resume_writing(self) -> None:
        log.debug("Resuming data transfer")
        self._can_write.set()

    async def drain(self) -> None:
        log.debug("Checking transfer")
        await self._can_write.wait()

    def _timeout(self) -> None:
        """Close connections upon timeout"""
        log.warning("Connection timeout, closing")
        self.transport.close()

    def connection_made(self, transport) -> None:
        self.transport = transport
        log.info(transport.get_extra_info('peername'))
        
    def error(self, code: int, msg: str) -> None:
        self.transport.write(f'{code} {msg}\r\n'.encode('utf-8'))
        log.error(f"{code} {msg}")
        self.transport.close()
        
    def send_file(self, path):
        path = getcwd() + normpath(path)
        log.debug(path)
        for filename in [path + "index.gmi", path]:
            if exists(filename):
                meta = guess_type(filename)[0]
                if meta is None:
                    meta = "application/octet-stream"
                status = 20
                self.transport.write(f'{status} {meta}\r\n'.encode('utf-8'))
                count = 0
                with open(filename, 'rb') as file:
                    while chunk := file.read(32768):
                        self.transport.write(chunk)
                        count = count + len(chunk)
                        log.debug(count)
                log.info(f"{status} {meta} {count}")
                self.transport.close()
                return
        self.error(40, "File not found")
        
    def data_received(self, data) -> None:
        self.timeout_handle.cancel()
        log.debug(f"{data}")
        if len(data) >= 7 and data[:7] != b'gemini:':
            self.error(59, 'Only Gemini requests are supported')
            return
        crlf_pos = data.find(b'\r\n')
        if crlf_pos >= 0:
            request = data[:crlf_pos].decode('utf-8')
            url = urlparse(request)
            self.send_file(url.path)
        else:
            self.error(59, 'Bad Request')


async def main(host, port) -> None:
    add_type("text/gemini", ".gmi")
    add_type("text/markdown", ".md")
    loop = get_running_loop()
    context = create_default_context(Purpose.CLIENT_AUTH)
    context.load_cert_chain("gemini.crt", "gemini.key")
    server = await loop.create_server(GeminiProtocol, host, port, ssl=context)
    log.info(f"('{host}', {port})")
    await server.serve_forever()

if __name__=="__main__":
    run(main(environ.get("BIND_ADDRESS", '127.0.0.1'), 1965))
    
