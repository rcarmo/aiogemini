#!/bin/env python3 

from asyncio import Protocol, Event, get_running_loop, run
from ssl import create_default_context, Purpose
from urllib.parse import urlparse

TIMEOUT = 1

class GeminiProtocol(Protocol):
    def __init__(self):
        # Enable flow control
        self._can_write = Event()
        self._can_write.set()
        # Enable timeouts
        loop = get_running_loop()
        self.timeout_handle = loop.call_later(TIMEOUT, self._timeout)
        print("set")

    def pause_writing(self) -> None:
        print("pause")
        self._can_write.clear()

    def resume_writing(self) -> None:
        print("resume")
        self._can_write.set()

    async def drain(self) -> None:
        print("drain")
        await self._can_write.wait()

    def _timeout(self) -> None:
        """Close connections upon timeout"""
        print("timeout")
        self.transport.close()

    def connection_made(self, transport) -> None:
        self.transport = transport
        print("connected")

    def error(self, code: int, msg: str) -> None:
        self.transport.write(f'{code} {msg}\r\n'.encode('utf-8'))
        self.transport.close()

    def data_received(self, data) -> None:
        self.timeout_handle.cancel()
        print(f"got data {data}")
        if len(data) >= 7 and data[:7] != b'gemini:':
            self.error(59, 'Only Gemini requests are supported')
            return
        crlf_pos = data.find(b'\r\n')
        if crlf_pos >= 0:
            request = data[:crlf_pos].decode('utf-8')
            url = urlparse(request)
            path = url.path
            # TODO: actually use path
            meta = 'text/gemini;charset=utf-8'
            status = 20
            data = "# Hello World\r\n=> / Homepage\r\n"
            self.transport.write(f'{status} {meta}\r\n{data}'.encode('utf-8'))
            self.transport.close()
        else:
            self.error(59, 'Bad Request')


async def main(host, port) -> None:
    loop = get_running_loop()
    context = create_default_context(Purpose.CLIENT_AUTH)
    context.load_cert_chain("gemini.crt", "gemini.key")
    server = await loop.create_server(GeminiProtocol, host, port, ssl=context)
    print("entering loop")
    await server.serve_forever()

if __name__=="__main__":
    run(main('127.0.0.1', 1965))
