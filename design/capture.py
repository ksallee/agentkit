#!/usr/bin/env python3
"""Capture every screen `design/screens.json` names, as two artboard files each.

    uv run --with playwright python design/capture.py
    uv run --with playwright python design/capture.py --only Inbox
    uv run --with playwright python design/capture.py --base http://localhost:4173

The python pack's driver. `design/capture.mjs` is the typescript pack's, and
`design/capture.js` is the contract they share, so both write the same bytes
from the same screen. `design-process` step 6 is the method this runs.

This points at a URL and never starts the app. Building a fixture and starting a
dev server is the most project-specific thing a capture does, and a template
that guessed at it would guess wrong: `screens.json` names where the app
answers, and the project owns whatever runs there.

Two files per screen, from one page load:

    <Name>.dc.html       curated computed styles, tokens written back as var(),
                         one inline style per node. What the canvas opens.
    <Name>.classes.html  the markup with the app's stylesheet carried whole.
                         Smaller and pixel exact, so a pull request diffs this
                         one and reads the design change.

Neither is hand-edited. Both carry a provenance stamp on the root, so a
designer who duplicates an artboard in the canvas and works on the copy can
tell when its reference has moved.

Every artboard is measured against the live page before it is written, and a
box further than one grid unit from the app fails the run. An eye passes a
capture that is two pixels out, and two pixels out is what somebody sees
without knowing why.

Playwright is the one third-party dependency in a project that captures. It is
imported inside `main`, so `--help` answers on an interpreter with nothing
installed and `bin/check-probes` can run this file's probe.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "capture.js"
SCREENS = HERE / "screens.json"

# Chrome lays out on a 1/64 px grid, so one grid unit is the smallest
# difference a box can have and the tightest tolerance worth asserting.
GRID = 1 / 64

# The stamp's digest is the sha256 of the classes form's markup, first 16 hex
# characters. `design/capture.mjs` computes the same field the same way, and
# `design/capture.js` carries the definition.
DIGEST_CHARS = 16

# A screen that has not painted in this long is a screen that never will, and a
# run that hangs on it reports nothing at all.
LOAD_TIMEOUT_MS = 30_000


def load_screens(path: Path) -> dict:
    """The capture's inputs, read from `screens.json`.

    Naming the screens in a committed file rather than in arguments is what
    makes a rerun reproducible without somebody remembering a command. Every
    name in it is owned by the capture, and nothing else in the design
    directory may write `<Name>.dc.html` or `<Name>.classes.html`.
    """
    try:
        declared = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"{path} could not be read: {exc}") from exc
    except ValueError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}") from exc
    if not declared.get("screens"):
        raise SystemExit(f"{path} names no screens. Add one, with a name and a route.")
    return declared


def frame(screen: dict, declared: dict) -> tuple[int, int]:
    """The viewport one screen opens at, from the screen or the file's default."""
    default = declared.get("viewport", {})
    return (
        int(screen.get("width", default.get("width", 1440))),
        int(screen.get("height", default.get("height", 1000))),
    )


def commit(root: Path, ignore: Path) -> str:
    """The commit a capture came from, marked `-dirty` when the tree has moved.

    A stamp that names a commit the screen was never at is worse than one that
    says the tree was dirty, because the whole drift story rests on it. Changes
    under the design directory are excluded: a capture writes there, so a second
    run in one session would otherwise report every screen dirty.
    """
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if head.returncode != 0:
        return ""
    rel = ignore.relative_to(root).as_posix() if ignore.is_relative_to(root) else None
    moved = [
        line
        for line in status.stdout.splitlines()
        if line.strip() and (rel is None or rel not in line[3:])
    ]
    return head.stdout.strip() + ("-dirty" if moved else "")


def answering(base: str) -> bool:
    """Whether anything serves the base URL."""
    try:
        with urllib.request.urlopen(base, timeout=5):
            return True
    except urllib.error.HTTPError:
        return True
    except (OSError, ValueError):
        return False


def deviation(a: dict, b: dict) -> float:
    return max(abs(x - y) for x, y in zip(a["box"], b["box"], strict=True))


def show(entry: dict) -> str:
    return f"{entry['tag']} " + " ".join(f"{v:.4f}" for v in entry["box"])


def capture(page, contract: str, screen: dict, stamp: dict, title: str) -> dict:
    """Both forms of one screen, from one page load.

    Order is the correctness of this function. `boxes` and `classes` only read.
    `curated` rewrites every style attribute in the document, so a classes form
    taken after it would carry the curated one's inline styles.
    """
    page.add_script_tag(content=contract)
    truth = page.evaluate("() => agentkitCapture.boxes()")
    forms = {
        "classes": page.evaluate("() => agentkitCapture.classes()"),
        "curated": page.evaluate("() => agentkitCapture.curated()"),
    }
    stamp = stamp | {"digest": hashlib.sha256(forms["classes"]["body"].encode()).hexdigest()[:DIGEST_CHARS]}
    written = {}
    for form, data in forms.items():
        if data["lost"]:
            raise SystemExit(f"{screen['name']}: {data['lost']} stylesheet(s) could be neither read nor linked")
        written[form] = {
            "canvas": page.evaluate(
                "([form, stamp, title]) => agentkitCapture.assemble(form, stamp, title)",
                [data, stamp, title],
            ),
            "plain": page.evaluate(
                "([form, stamp]) => agentkitCapture.plain(form, stamp)", [data, stamp]
            ),
        }
    return {"truth": truth, "written": written, "stamp": stamp}


def check(browser, viewport: dict, contract: str, plain: str, truth: list[dict]) -> tuple[int, float, list[str]]:
    """Reload one written artboard and measure it against the live page.

    The artboard root is one element the live page does not have, so the
    comparison drops it. Returns how many boxes moved, the worst distance, and
    the five worst as lines a person can read.
    """
    page = browser.new_page(viewport=viewport)
    page.set_content(plain, wait_until="networkidle")
    page.evaluate("() => document.fonts.ready")
    page.add_script_tag(content=contract)
    got = page.evaluate("() => agentkitCapture.boxes()")[1:]
    page.close()
    if len(got) != len(truth):
        return len(truth), float("inf"), [f"{len(got)} elements against {len(truth)} live"]
    off = sorted(
        ({"live": a, "here": b, "by": deviation(a, b)} for a, b in zip(truth, got, strict=True)),
        key=lambda d: -d["by"],
    )
    moved = [d for d in off if d["by"] > 0]
    over = [d for d in moved if d["by"] > GRID + 1e-9]
    lines = [f"off {d['by']:.4f}\n    live {show(d['live'])}\n    here {show(d['here'])}" for d in over[:5]]
    return len(moved), (off[0]["by"] if off else 0.0), lines


def table(rows: list[dict]) -> str:
    """One line per file written, with the numbers a reader checks."""
    columns = ["screen", "form", "file", "bytes", "elements", "moved", "worst px", "var()"]
    widths = [max(len(c), *(len(str(r[c])) for r in rows)) for c in columns]
    head = "  ".join(c.ljust(w) for c, w in zip(columns, widths, strict=True))
    body = [
        "  ".join(str(row[c]).ljust(w) for c, w in zip(columns, widths, strict=True)) for row in rows
    ]
    return "\n".join([head, "  ".join("-" * w for w in widths), *body])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Capture the screens design/screens.json names.")
    ap.add_argument("--screens", type=Path, default=SCREENS, help="The screen list. Default: design/screens.json.")
    ap.add_argument("--only", help="Capture one screen by name.")
    ap.add_argument("--base", help="Where the app answers. Default: the base in the screen list.")
    ap.add_argument("--out", type=Path, help="Where the artboards land. Default: beside the screen list.")
    args = ap.parse_args(argv)

    declared = load_screens(args.screens)
    base = (args.base or declared.get("base", "")).rstrip("/")
    if not base:
        raise SystemExit(f"{args.screens} names no base URL, and --base was not given.")
    out = args.out or args.screens.resolve().parent
    wanted = [s for s in declared["screens"] if args.only in (None, s["name"])]
    if not wanted:
        known = ", ".join(s["name"] for s in declared["screens"])
        raise SystemExit(f"no screen named {args.only}. Known: {known}")

    if not answering(base):
        raise SystemExit(
            f"nothing answered at {base}. This capture points at a running app and never starts one.\n"
            f"Start the app, then rerun. {args.screens} names what it expects."
        )

    from playwright.sync_api import sync_playwright

    contract = CONTRACT.read_text(encoding="utf-8")
    stamped = commit(Path.cwd(), out)
    at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows: list[dict] = []
    bad = 0

    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        for screen in wanted:
            width, height = frame(screen, declared)
            viewport = {"width": width, "height": height}
            page = browser.new_page(viewport=viewport)
            errors: list[str] = []
            # The sink is bound as a default, so the handler writes to this
            # screen's list rather than to whichever one the loop is on when it
            # fires.
            page.on("pageerror", lambda exc, sink=errors: sink.append(str(exc)))
            response = page.goto(base + screen["route"], wait_until="networkidle", timeout=LOAD_TIMEOUT_MS)
            if response is None or not response.ok:
                raise SystemExit(f"{screen['route']} answered {response.status if response else 'nothing'}")
            page.evaluate("() => document.fonts.ready")
            # A screen that threw while mounting still renders its server
            # markup, so the capture would look right and carry a half-mounted
            # component.
            if errors:
                raise SystemExit(f"{screen['route']} threw: {errors[0]}")

            stamp = {
                "route": screen["route"],
                "commit": stamped,
                "at": at,
                "viewport": f"{width}x{height}",
                "digest": "",
            }
            result = capture(page, contract, screen, stamp, screen.get("title", screen["name"]))
            page.close()

            for form, docs in result["written"].items():
                name = f"{screen['name']}.{'classes' if form == 'classes' else 'dc'}.html"
                moved, worst, lines = check(browser, viewport, contract, docs["plain"], result["truth"])
                if lines:
                    bad += 1
                    print(f"{screen['name']} {form}: {len(lines)} box(es) further than one grid unit from the app")
                    for line in lines:
                        print(f"    {line}")
                (out / name).write_text(docs["canvas"], encoding="utf-8")
                rows.append(
                    {
                        "screen": screen["name"],
                        "form": form,
                        "file": name,
                        "bytes": len(docs["canvas"]),
                        "elements": len(result["truth"]),
                        "moved": f"{moved}/{len(result['truth'])}",
                        "worst px": f"{worst:.4f}",
                        "var()": docs["canvas"].count("var(--"),
                    }
                )
        browser.close()

    print(f"\n{stamped or 'no commit'}  {len(wanted)} screen(s) -> {out}\n")
    print(table(rows))
    if bad:
        raise SystemExit(f"\n{bad} artboard(s) do not match the app.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
