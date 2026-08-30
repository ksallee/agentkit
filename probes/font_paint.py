#!/usr/bin/env python3
"""Print what `document.fonts.check` and a width probe each report for one page.

    python3 probes/font_paint.py
    python3 probes/font_paint.py --port 8043 --timeout 300

Rule 9. `design-process` step 6 asserts that the intended font is painting, and
`document.fonts.check` answers a different question: whether a matching face is
available to the font set. Only a browser settles what it returns, so this
serves `font_paint.html`, which runs both assertions against five families and
posts its numbers back here.

The families, one per failure the assertion has to separate:

- `ProbeBroken`, declared with a `src` this server answers 404 to
- `ProbeLocalUsed`, declared `local(Georgia)` and painted on the page
- `ProbeLocalUnused`, declared `local(Courier New)` with no element using it
- `Georgia`, installed and never declared
- `Nonexistent Face Qz`, nowhere

Rule 9 also says a probe is standard library only, so that it runs before the
project installs. No browser driver satisfies both halves. What this does
instead: the server is stdlib, and the operator's own browser is the runtime.
Open the URL it prints. The page posts its report to `result`, this prints it
and exits. Opening `probes/font_paint.html` from disk prints the same report
into the page, minus the 404 on the broken face, which misses under `file://`
too. Headless Chrome reaches it the same way a person does:

    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\
      --headless --disable-gpu --virtual-time-budget=5000 http://127.0.0.1:8043/

Prints. Writes nothing.
"""

from __future__ import annotations

import argparse
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PAGE = Path(__file__).resolve().parent / "font_paint.html"

# Issue 43, so two probes left running do not collide.
DEFAULT_PORT = 8043

# Long enough for a person to open a browser, short enough that a forgotten
# probe frees the port on its own.
DEFAULT_TIMEOUT_SECONDS = 300

# One poll per second, so the deadline below is honoured within a second of an
# idle server.
POLL_SECONDS = 1


class Handler(BaseHTTPRequestHandler):
    """Three routes: the page, the 404 that breaks the webfont, the report."""

    # Set by do_POST, read by the loop in main().
    report: str | None = None

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path in ("/", "/font_paint.html"):
            self.send(200, "text/html; charset=utf-8", PAGE.read_bytes())
            return
        # The deliberately broken webfont link, and every other path with it.
        # A face whose src 404s is the case the whole probe is built around.
        self.send(404, "text/plain; charset=utf-8", b"no such file\n")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        Handler.report = self.rfile.read(length).decode("utf-8", "replace")
        self.send(204, "text/plain; charset=utf-8", b"")

    def send(self, status: int, kind: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        # A cached page hides an edit to the fixture behind a reload that looks
        # like a rerun.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        """Silence the request log, so the report is the only thing printed."""


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe what a browser reports about a painted font.")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = ap.parse_args()

    if not PAGE.exists():
        print(f"  {PAGE} is missing. The probe is the page plus this server.")
        return 1

    try:
        server = HTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as exc:
        print(f"  127.0.0.1:{args.port} did not bind: {exc}")
        return 1

    url = f"http://127.0.0.1:{args.port}/"
    print(f"Open {url}")
    print(f"The page posts its report back here. Waiting up to {args.timeout}s.\n")

    server.timeout = POLL_SECONDS
    deadline = time.monotonic() + args.timeout
    try:
        while Handler.report is None and time.monotonic() < deadline:
            server.handle_request()
    except KeyboardInterrupt:
        print("\n  stopped before the page reported")
        return 1
    finally:
        server.server_close()

    if Handler.report is None:
        print(f"  nothing posted to {url}result in {args.timeout}s")
        return 1
    print(Handler.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
