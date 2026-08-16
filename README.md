turnbreak — show something worth reading while your coding agent works

Supported formats

- Markdown (.md) and plain text (.txt): rendered in the shell and counted directly.
- HTML (.html): stripped of markup and rendered; word count uses trafilatura extraction.
- PDF (.pdf): embedded into the shell as base64 bytes so the page, buttons, title, and favicon stay under the skill's control. A small text-extraction step (pypdf) counts words for a read-time estimate; if extraction fails the PDF is still shown but no read-time estimate is shown.

Not supported yet

- EPUB: browsers lack native EPUB rendering and EPUB support is planned but not implemented in v0.1.0.

See TASKS.md for the full project plan and tests.
