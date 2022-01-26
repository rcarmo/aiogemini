# `aiogemini`

This is a barebones `asyncio` server for the [Gemini protocol](https://gemini.circumlunar.space/), written as a `Protocol` class for a quick hack so I could play around with the protocol myself.

## Roadmap

Things I may be adding (if time permits), in reverse order of priority:

* [ ] Plugins for handling specific routes
* [ ] Protocol extensions (length, timestamp, etc.)
* [ ] Proper argument and certificate handling
* [x] Serve media files
* [ ] Directory indexes
* [ ] Frontmatter skipping in `text/gemini` files
* [x] Basic `text/gemini` handling
* [x] Proper logging
* [x] Barebones "Hello World" server

## Out of Scope

Things I also find interesting, but have no immediate plans to add:

* Dual stack (HTTPS support)
* SNI virtual hostnames
* Titan upload support
* Content conversion (Markdown to Gemini, etc.)
