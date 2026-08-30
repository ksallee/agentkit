#!/usr/bin/env python3
"""Rule 9 over the capture: drive `design/capture.py` against a page served here.

    probes/design_capture.py            # capture one throwaway page, print what came back
    probes/design_capture.py --keep     # leave the artboards on disk and name the directory

Playwright and a Chromium build are the first hard third-party dependency in
anything agentkit ships, and #43 avoided one deliberately by serving a page for
a person to open. A capture cannot: it reads computed styles out of a real
engine. This probe is what runs that engine here.

agentkit's own `surface` is `none` and it draws no screens, so without this the
repository would ship a capture it never executes. The page below is a
throwaway with a stylesheet, a `:root` token block and nested boxes whose
padding lives only in the sheet, which is the shape the two forms differ on.

What it asserts, and prints the number behind each:

    two files per screen, from one page load
    the `.dc.html` carries inline styles a properties panel could write to,
      where the served markup carries none
    the `.classes.html` is smaller and keeps the app's stylesheet
    both carry the five-field provenance stamp, with one digest between them

Standard library only, and the driver runs in a subprocess through uv, so this
file parses and answers `--help` on an interpreter with nothing installed.
`bin/check-probes` runs exactly that.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVER = ROOT / "design" / "capture.py"

# The stamp's fields, in the order `design/capture.js` writes them.
STAMP = ("route", "commit", "at", "viewport", "digest")

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Throwaway</title>
  <link rel="stylesheet" href="./app.css">
</head>
<body>
  <main class="card">
    <h1 class="answer">4h 12m</h1>
    <p class="sub">unaccounted, 25 August</p>
    <div class="row"><span class="chip">acme</span><span class="chip">elevo</span></div>
  </main>
</body>
</html>
"""

# Every length and colour lives in the sheet, and nothing in the markup carries
# a style attribute. That is the whole difference the two forms exist for: a
# properties panel has nothing to read here, and the curated form gives it
# something.
SHEET = """:root {
  --bg: #ffffff;
  --ink: #111111;
  --ink2: #555555;
  --line: #d9d9d9;
  --panel: #f3f3f3;
  --radius: 6px;
}
body { margin: 0; background: var(--bg); color: var(--ink);
  font-family: -apple-system, Helvetica, Arial, sans-serif; }
.card { width: 520px; padding: 40px; display: flex; flex-direction: column; gap: 12px;
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); }
.answer { margin: 0; font-size: 40px; font-weight: 600; line-height: 1.2; }
.sub { margin: 0; font-size: 15px; color: var(--ink2); }
.row { display: flex; gap: 8px; }
.chip { padding: 4px 10px; border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--bg); font-size: 13px; }
"""


def serve(directory: Path) -> tuple[socketserver.TCPServer, str]:
    """A throwaway page on a free port, in a thread, until the caller shuts it down."""
    handler = functools.partial(Quiet, directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


class Quiet(http.server.SimpleHTTPRequestHandler):
    """`SimpleHTTPRequestHandler` with its request log off, so the probe's output is its own."""

    def log_message(self, *args: object) -> None:
        return


def stamp_of(text: str) -> dict[str, str]:
    """The provenance stamp read off an artboard's root element."""
    found = {}
    for field in STAMP:
        match = re.search(rf'data-captured-{field}="([^"]*)"', text)
        if match:
            found[field] = match.group(1)
    return found


def report(ok: bool, line: str) -> bool:
    print(f"  {'pass' if ok else 'FAIL'}  {line}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Capture one throwaway page and print what was written.")
    ap.add_argument("--keep", action="store_true", help="Leave the artboards on disk and name the directory.")
    args = ap.parse_args()

    if not shutil.which("uv"):
        print("uv is not on PATH, and the driver runs through it. Install uv, then rerun.")
        return 1

    work = Path(tempfile.mkdtemp(prefix="agentkit-capture-"))
    page = work / "page"
    page.mkdir()
    (page / "index.html").write_text(PAGE, encoding="utf-8")
    (page / "app.css").write_text(SHEET, encoding="utf-8")

    httpd, base = serve(page)
    screens = work / "screens.json"
    screens.write_text(
        json.dumps(
            {
                "version": 1,
                "base": base,
                "viewport": {"width": 900, "height": 600},
                "screens": [{"name": "Throwaway", "route": "/index.html", "title": "Throwaway"}],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"page     {page}")
    print(f"serving  {base}")
    print(f"driver   {DRIVER}\n")
    done = subprocess.run(
        [
            "uv", "run", "--quiet", "--with", "playwright", "python", str(DRIVER),
            "--screens", str(screens), "--out", str(work),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    httpd.shutdown()
    print(done.stdout.strip())
    if done.returncode != 0:
        print(done.stderr.strip())
        print("\nThe driver did not finish. Nothing below was asserted.")
        return 1

    dc = work / "Throwaway.dc.html"
    classes = work / "Throwaway.classes.html"
    print(f"\nwrote    {dc.name} {dc.stat().st_size} bytes, {classes.name} {classes.stat().st_size} bytes")

    dc_text = dc.read_text(encoding="utf-8")
    classes_text = classes.read_text(encoding="utf-8")
    served = (page / "index.html").read_text(encoding="utf-8")
    dc_inline = dc_text.count('style="')
    classes_inline = classes_text.count('style="')
    dc_stamp = stamp_of(dc_text)
    classes_stamp = stamp_of(classes_text)

    print("\nthe contract")
    held = [
        report(dc.is_file() and classes.is_file(), "two files came out of one page load"),
        report(
            dc_inline > classes_inline and served.count('style="') == 0,
            f"{dc_inline} inline styles in the .dc.html, {classes_inline} in the .classes.html, "
            f"{served.count('style=')} in the served markup",
        ),
        report(
            classes.stat().st_size < dc.stat().st_size,
            f"the .classes.html is {dc.stat().st_size / classes.stat().st_size:.1f} times smaller",
        ),
        report(".card {" in classes_text, "the .classes.html carries the app's stylesheet whole"),
        report(
            dc_text.count("var(--") > 0,
            f"{dc_text.count('var(--')} token references written back into the .dc.html",
        ),
        report(
            set(dc_stamp) == set(STAMP) and set(classes_stamp) == set(STAMP),
            f"both roots carry the stamp: {', '.join(sorted(dc_stamp))}",
        ),
        report(
            bool(dc_stamp.get("digest")) and dc_stamp.get("digest") == classes_stamp.get("digest"),
            f"one digest between the pair: {dc_stamp.get('digest', 'absent')}",
        ),
    ]

    print(f"\nstamp    {json.dumps(dc_stamp, indent=2)}")
    if args.keep:
        print(f"\nkept     {work}")
    else:
        shutil.rmtree(work, ignore_errors=True)
    return 0 if all(held) else 1


if __name__ == "__main__":
    sys.exit(main())
