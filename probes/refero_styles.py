#!/usr/bin/env python3
"""Print what styles.refero.design serves for a design system, and in what form.

    python3 probes/refero_styles.py
    python3 probes/refero_styles.py --style 031056ff-7af1-46db-8daa-115f731c5d26

Rule 9. #12 weighed the catalogue as the source of the `design-references`
list, and the question is whether a `DESIGN.md` can be read the way a probe
reads any other payload: one call, a document out.

Five calls. The index, for how many styles it links and under what path. One
style page, for its size, its content type and the top-level keys of the design
system embedded in it. The two paths a `DESIGN.md` would sit at if the site
served one as a file. Then the page the site points at for its MCP server,
which is where a project that turns the option on gets wired up.

Prints. Writes nothing. Standard library, so it runs before the project does.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request

BASE = "https://styles.refero.design"
MCP = "https://refero.design/mcp"

# An MCP server is addressed by URL, so a page offering one either carries the
# address or hands it out somewhere a fetch cannot follow.
MCP_URL = re.compile(r"https://[a-z0-9.-]*refero\.design/[a-z0-9/_-]*mcp[a-z0-9/_-]*")

# A UUID under /style/. The index links every catalogue entry this way.
STYLE_LINK = re.compile(r"/style/([0-9a-f-]{36})")

# The page is a Next.js document with its data inlined as escaped JSON. These
# are the keys a design system is described under, and finding them is what
# says the payload is a system rather than a screenshot with a caption.
SYSTEM_KEYS = ("colors", "typography", "spacing", "shapes", "elevation", "components")

TIMEOUT_SECONDS = 30


def get(url: str) -> tuple[int, str, bytes]:
    """Status, content type and body. A failed call reports instead of raising."""
    request = urllib.request.Request(url, headers={"User-Agent": "agentkit-probe"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as answer:
            return answer.status, answer.headers.get("Content-Type", ""), answer.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  {url} did not answer: {exc}")
        return 0, "", b""


def show(label: str, url: str) -> bytes:
    status, kind, body = get(url)
    print(f"\n{label}\n  {url}")
    print(f"  {status} {kind} {len(body)} bytes")
    return body


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe what refero serves for one design system.")
    ap.add_argument("--style", default="031056ff-7af1-46db-8daa-115f731c5d26", help="A style id.")
    args = ap.parse_args()

    index = show("The index", BASE + "/")
    ids = sorted(set(STYLE_LINK.findall(index.decode("utf-8", "replace"))))
    print(f"  {len(ids)} distinct /style/<uuid> link(s) on the first page")

    page = show("One style", f"{BASE}/style/{args.style}")
    text = page.decode("utf-8", "replace")
    found = [key for key in SYSTEM_KEYS if f'\\"{key}\\":' in text or f'"{key}":' in text]
    print(f"  design system keys present: {', '.join(found) or 'none'}")
    print(f"  the string DESIGN.md appears {text.count('DESIGN.md')} time(s)")

    for label, url in (
        ("As a file, under the style", f"{BASE}/style/{args.style}/DESIGN.md"),
        ("As a file, by suffix", f"{BASE}/style/{args.style}.md"),
    ):
        body = show(label, url)
        # A soft 404 answers 200 with the application shell, so the size beside
        # the style page above separates a document from a miss.
        print(f"  markdown heading in the body: {body.lstrip().startswith(b'#')}")

    banner = show("The MCP server, as the site offers it", MCP)
    endpoints = sorted(set(MCP_URL.findall(banner.decode("utf-8", "replace"))))
    print(f"  endpoint(s) in the served HTML: {', '.join(endpoints) or 'none'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
