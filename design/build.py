"""Write every wireframe artboard, and the canvas layout that holds them.

    python3 design/build.py

`design-process` step 3: one generator writes every frame, so a number or a
label changes in one place and the frames stay consistent. Greyscale on
purpose, because structure and behaviour come first and colour and the type
pair stay the designer's call. Real numbers, scaled from a measurement, never
lorem ipsum.

What ships here is the method's half. The constants below are defaults a
project edits in place, `Palette.dc.html` renders whatever they say, and
`canvas.json` lays out every artboard beside the screens `design/capture.py`
writes. The components a project draws with are the project's, and they are
found while drawing rather than guessed at here: a shipped table, chart or row
would be one project's shape imposed on every other.

A number appears once. Every grey is read out of `GREYS`, every type size out
of `TYPE`, every step out of `SPACE`, and the sheet renders what it finds, so
changing a value changes the artboard and the documentation of that value
together.

A rerun is byte identical. Nothing here reads a clock or a commit, so a
generated artboard changes only when the generator does, and a diff on this
directory is a design change every time.

`design/build.mjs` is the same generator for a project whose pack is
typescript, and `tests/test_design.py` holds them to the same bytes.

Standard library only, so this runs on a machine that has installed nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# The frame every screen artboard opens at, and the space between two of them
# on the canvas. A project working at another size changes these two numbers.
FRAME_W, FRAME_H = 1440, 1000
GUTTER = 120

# A sheet is wider than a screen, because it draws several things side by side.
SHEET_W, SHEET_H = 1440, 1000

# The greys, each with the one meaning it carries. `DESIGNER.md` says one
# meaning per colour, and a grey is a colour. A project that needs a seventh
# adds it here with what it means, and the palette sheet grows a row.
GREYS = [
    ("ink", "#111111", "text, and the answer a screen leads with"),
    ("ink2", "#555555", "secondary text"),
    ("ink3", "#8a8a8a", "a label read once"),
    ("line", "#d9d9d9", "a border"),
    ("panel", "#f3f3f3", "a surface above the page"),
    ("bg", "#ffffff", "the page"),
]
GREY = {name: value for name, value, _ in GREYS}

# The type scale, as (name, px, weight). Sizes are a scale rather than a list
# of one-off values, so a screen at a size nobody named is a screen to look at.
TYPE = [
    ("answer", 40, 600),
    ("heading", 20, 600),
    ("body", 15, 400),
    ("label", 13, 400),
    ("note", 11, 400),
]
SIZE = {name: px for name, px, _ in TYPE}

# The spacing scale. Every gap, pad and margin on an artboard is one of these.
SPACE = [4, 8, 12, 16, 24, 40]

RADIUS = 3

# A system stack on purpose. The type pair is the designer's call, and a
# generator that picked one would be making it.
SANS = "-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, Menlo, Consolas, monospace"

# The stamp on a generated artboard's root. A capture stamps a route, a commit
# and a time because its reference is a screen that moves on its own. A
# generated artboard has no such reference: this file is the reference. So the
# stamp names the function that drew it, the frame it was drawn at, and a
# digest of its own markup. A designer who duplicates an artboard in the canvas
# regenerates, compares digests, and learns whether the original moved. Neither
# a commit nor a timestamp would add anything the digest lacks, and both would
# churn every file on every run.
DIGEST_CHARS = 16


def esc(text: str) -> str:
    """HTML-escape, for anything that reaches an attribute or a text node."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def box(style: str, inner: str) -> str:
    return f'<div style="{style}">{inner}</div>'


def text(name: str, body: str, colour: str = "", extra: str = "") -> str:
    """One line at a named step of the type scale."""
    px = SIZE[name]
    weight = next(w for n, _, w in TYPE if n == name)
    style = f"font-size: {px}px; font-weight: {weight}; line-height: 1.3; color: {colour or GREY['ink']}"
    return box(style + (f"; {extra}" if extra else ""), body)


def stack(gap: int, inner: str, extra: str = "") -> str:
    style = f"display: flex; flex-direction: column; gap: {gap}px"
    return box(style + (f"; {extra}" if extra else ""), inner)


def row(gap: int, inner: str, align: str = "center") -> str:
    return box(f"display: flex; align-items: {align}; gap: {gap}px", inner)


def swatch(value: str, size: int) -> str:
    style = (
        f"width: {size}px; height: {size}px; flex: none; background: {value}; "
        f"border: 1px solid {GREY['line']}; border-radius: {RADIUS}px"
    )
    return box(style, "")


def mono(body: str, colour: str = "") -> str:
    style = f"font-family: {MONO}; font-size: {SIZE['label']}px; color: {colour or GREY['ink2']}"
    return box(style, body)


def section(title: str, note: str, inner: str) -> str:
    head = stack(SPACE[0], text("heading", esc(title)) + text("note", esc(note), GREY["ink3"]))
    return stack(SPACE[3], head + inner)


def artboard(name: str, title: str, body: str, width: int, height: int) -> str:
    """One `.dc.html` file: the stamp, then one root sized to its canvas slot.

    The same extension and the same root shape as a captured artboard, so the
    canvas and a pull request read one set of files. The prefix differs because
    the provenance differs: `data-captured-*` names a screen that ran,
    `data-generated-*` names the function that drew one that has not.

    The head loads `./support.js`, which the canvas editor serves beside the
    artboards. Without that line an artboard opens in the canvas as flat markup
    and nothing on it can be selected or edited.
    """
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:DIGEST_CHARS]
    root = (
        f"width: {width}px; height: {height}px; box-sizing: border-box; overflow: hidden; "
        f"padding: {SPACE[5]}px; display: flex; flex-direction: column; gap: {SPACE[4]}px; "
        f"background: {GREY['bg']}; color: {GREY['ink']}; font-family: {SANS}"
    )
    marks = (
        f'data-generated-by="{esc(name)}" '
        f'data-generated-viewport="{width}x{height}" '
        f'data-generated-digest="{digest}"'
    )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <title>{esc(title)}</title>
  <style>body {{ margin: 0; }}</style>
</helmet>
<!-- generated by={name} viewport={width}x{height} digest={digest} -->
<div {marks} style="{root}">
{body}
</div>
</x-dc>
</body>
</html>
"""


def palette_sheet() -> str:
    """The defaults this generator ships, rendered from the constants that hold them.

    The one artboard agentkit draws for a project, and the only one it can:
    every other frame needs components only the project has. This one documents
    the palette and the two scales by rendering them, so a project that edits a
    grey sees the edit on the artboard and in the legend at once.
    """
    greys = "".join(
        row(
            SPACE[2],
            swatch(value, SIZE["answer"])
            + stack(
                SPACE[0],
                text("label", esc(name)) + mono(esc(value)) + text("note", esc(meaning), GREY["ink3"]),
            ),
        )
        for name, value, meaning in GREYS
    )
    sizes = "".join(
        row(
            SPACE[3],
            box("width: 96px; flex: none", mono(f"{name} {px}"))
            + text(name, "Four hours on one project"),
        )
        for name, px, _ in TYPE
    )
    steps = "".join(
        row(
            SPACE[2],
            box("width: 40px; flex: none", mono(str(step)))
            + box(
                f"width: {step}px; height: {SPACE[2]}px; background: {GREY['ink3']}; border-radius: {RADIUS}px",
                "",
            ),
        )
        for step in SPACE
    )
    frame = mono(f"frame {FRAME_W}x{FRAME_H}, gutter {GUTTER}, radius {RADIUS}")

    body = stack(
        SPACE[5],
        stack(
            SPACE[1],
            text("answer", "Greyscale, and the two scales under it")
            + text(
                "body",
                "Every number on this sheet is read out of design/build.py. Edit a value there and "
                "this artboard says so on the next run. Colour and the type pair stay the "
                "designer's call, which is what step 3 means by greyscale on purpose.",
                GREY["ink2"],
                "max-width: 760px",
            ),
        )
        + row(
            SPACE[5],
            section("Greys", "one meaning each, and used nowhere else", stack(SPACE[2], greys))
            + stack(
                SPACE[5],
                section("Type", "a scale, so a one-off size is a thing to look at", stack(SPACE[2], sizes))
                + section("Space", "every gap, pad and margin is one of these", stack(SPACE[1], steps))
                + section("Frame", "what an artboard opens at", frame),
            ),
            "flex-start",
        ),
    )
    return body


# Every artboard this generator writes, as file name to the function that draws
# it. A project adds a row and a function, and both the file and its slot in
# `canvas.json` follow. One entry point is the whole point of step 3.
ARTBOARDS = {
    "Palette.dc.html": ("Greyscale, and the two scales under it", SHEET_W, SHEET_H, palette_sheet),
}


def captured(screens: Path) -> list[tuple[str, str, int, int]]:
    """The names `design/capture.py` owns, as slots to reserve rather than draw.

    A capture that has failed, or that has never run, must not be able to move
    an artboard this file wrote, and two writers on one file is the thing to
    avoid. The slot's size is the viewport the capture opens the screen at, so a
    frame changed in `screens.json` takes effect on the next capture.
    """
    try:
        declared = json.loads(screens.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    default = declared.get("viewport", {})
    return [
        (
            f"{screen['name']}.dc.html",
            screen.get("title", screen["name"]),
            int(screen.get("width", default.get("width", FRAME_W))),
            int(screen.get("height", default.get("height", FRAME_H))),
        )
        for screen in declared.get("screens", [])
    ]


def canvas(drawn: list[tuple[str, str, int, int]], reserved: list[tuple[str, str, int, int]]) -> dict:
    """The layout: one row of drawn artboards, one row of captured screens."""
    boards = []
    x = 0
    for file, title, width, height in drawn:
        boards.append({"file": file, "x": x, "y": 0, "w": width, "h": height, "title": title})
        x += width + GUTTER
    tall = max([height for _, _, _, height in drawn], default=0)
    x = 0
    for file, title, width, height in reserved:
        boards.append({"file": file, "x": x, "y": tall + GUTTER, "w": width, "h": height, "title": title})
        x += width + GUTTER
    return {"artboards": boards}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write every wireframe artboard and the canvas layout.")
    ap.add_argument("--out", type=Path, default=HERE, help="Where the artboards land. Default: beside this file.")
    ap.add_argument(
        "--screens",
        type=Path,
        default=HERE / "screens.json",
        help="The capture's screen list, whose names this file reserves and never writes.",
    )
    args = ap.parse_args(argv)

    reserved = captured(args.screens)
    clash = {file for file, _, _, _ in reserved} & set(ARTBOARDS)
    if clash:
        raise SystemExit(f"the capture owns {', '.join(sorted(clash))}. Remove them from ARTBOARDS.")

    args.out.mkdir(parents=True, exist_ok=True)
    drawn = []
    for file, (title, width, height, draw) in ARTBOARDS.items():
        (args.out / file).write_text(artboard(draw.__name__, title, draw(), width, height), encoding="utf-8")
        drawn.append((file, title, width, height))

    layout = json.dumps(canvas(drawn, reserved), indent=2) + "\n"
    (args.out / "canvas.json").write_text(layout, encoding="utf-8")

    print(f"wrote {len(ARTBOARDS)} artboard(s) and canvas.json to {args.out}")
    if reserved:
        print(f"reserved {len(reserved)} slot(s) for the capture: {', '.join(f for f, _, _, _ in reserved)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
