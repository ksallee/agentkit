"""The design directory a project is seeded with.

Nothing here launches a browser. `probes/design_capture.py` does that, and
`bin/check-probes` runs its `--help` on every gate run. What is left is the
half that can drift silently: two drivers, one contract, and a probe asserting
a stamp all three have to spell the same way.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "design"
CONTRACT = DESIGN / "capture.js"
SCREENS = DESIGN / "screens.json"
DRIVERS = (DESIGN / "capture.py", DESIGN / "capture.mjs")
BUILD_PY = DESIGN / "build.py"
BUILD_MJS = DESIGN / "build.mjs"
PROBE = ROOT / "probes" / "design_capture.py"

# `bin/adopt` carries no extension, because it is run rather than imported
# everywhere except in a test.
_loader = SourceFileLoader("adopt", str(ROOT / "bin" / "adopt"))
_spec = importlib.util.spec_from_loader("adopt", _loader)
adopt = importlib.util.module_from_spec(_spec)
sys.modules["adopt"] = adopt
_loader.exec_module(adopt)

# The pair the whole workflow rests on: one artifact to edit, one to review.
FORMS = (".dc.html", ".classes.html")


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def stamp_fields() -> list[str]:
    """The stamp's fields, read off the list `design/capture.js` writes them from."""
    found = re.search(r"const marks = \[([^\]]*)\]", text(CONTRACT))
    assert found, "capture.js no longer builds the stamp from a list of field names"
    return re.findall(r"'([a-z]+)'", found.group(1))


class TestTheContract:
    def test_it_returns_the_five_functions_a_driver_calls(self):
        returned = re.findall(r"return \{([^}]*)\};", text(CONTRACT))[-1]
        assert {n.strip() for n in returned.split(",")} == {"boxes", "classes", "curated", "assemble", "plain"}

    def test_the_stamp_carries_a_digest(self):
        """A commit alone cannot tell a duplicated artboard its reference moved over a dirty tree."""
        assert "digest" in stamp_fields()

    def test_every_stamp_field_is_written_as_an_attribute_and_a_comment(self):
        body = text(CONTRACT)
        assert body.count("data-captured-${key}") == 1
        for field in stamp_fields():
            assert f"'{field}'" in body


class TestBothDriversAgree:
    """A python project and a typescript project write the same artboard or the split is a lie."""

    def test_each_one_reads_the_shared_contract(self):
        for driver in DRIVERS:
            assert "capture.js" in text(driver)
            assert "agentkitCapture" in text(driver)

    def test_each_one_builds_every_stamp_field(self):
        for driver in DRIVERS:
            body = text(driver)
            for field in stamp_fields():
                assert re.search(rf"\b{field}\b", body), f"{driver.name} names no {field}"

    def test_each_one_takes_the_same_slice_of_the_digest(self):
        found = {re.search(r"DIGEST_CHARS = (\d+)", text(driver)).group(1) for driver in DRIVERS}
        assert found == {"16"}

    def test_each_one_writes_both_forms(self):
        for driver in DRIVERS:
            body = text(driver)
            for form in FORMS:
                assert form in body

    def test_neither_one_starts_the_app(self):
        """Settled at #83: the capture points at a URL, and the project owns what serves it."""
        for driver in DRIVERS:
            assert "never starts" in text(driver)


class TestTheScreenList:
    def test_it_parses_and_names_a_base_and_a_screen(self):
        declared = json.loads(text(SCREENS))
        assert declared["base"].startswith("http")
        assert declared["screens"]
        for screen in declared["screens"]:
            assert screen["name"] and screen["route"]

    def test_it_names_a_frame_size(self):
        declared = json.loads(text(SCREENS))
        assert declared["viewport"]["width"] and declared["viewport"]["height"]

    def test_the_note_says_the_capture_owns_those_names(self):
        """A seeded JSON file carries no comment, so the note is where the rule lives."""
        assert "nothing else may write" in json.loads(text(SCREENS))["note"]


class TestTheProbe:
    def test_it_asserts_the_stamp_the_contract_writes(self):
        found = re.search(r"STAMP = \(([^)]*)\)", text(PROBE)).group(1)
        assert re.findall(r'"([a-z]+)"', found) == stamp_fields()

    def test_it_drives_the_shipped_driver(self):
        assert 'DRIVER = ROOT / "design" / "capture.py"' in text(PROBE)

    def test_it_imports_nothing_a_bare_interpreter_lacks(self):
        """Rule 9, and `bin/check-probes` runs `--help` under exactly that interpreter."""
        imported = re.findall(r"^(?:import|from) (\w+)", text(PROBE), re.M)
        assert "playwright" not in imported


class TestTheGenerator:
    """`design-process` step 3: one generator writes every frame.

    Both copies run here and their bytes are compared, because a project
    receives one and the template carries two.
    """

    @staticmethod
    def run(command, out):
        return subprocess.run(
            [*command, "--out", str(out), "--screens", str(SCREENS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def files(out):
        return {p.name: p.read_bytes() for p in sorted(Path(out).iterdir())}

    def test_it_writes_an_artboard_and_a_canvas(self, tmp_path):
        done = self.run(["python3", str(BUILD_PY)], tmp_path)
        assert done.returncode == 0, done.stderr
        assert set(self.files(tmp_path)) == {"Palette.dc.html", "canvas.json"}

    def test_a_rerun_is_byte_identical(self, tmp_path):
        """A generated artboard changes when the generator does and never otherwise."""
        self.run(["python3", str(BUILD_PY)], tmp_path)
        first = self.files(tmp_path)
        self.run(["python3", str(BUILD_PY)], tmp_path)
        assert self.files(tmp_path) == first

    def test_both_copies_write_the_same_bytes(self, tmp_path):
        node = shutil.which("node")
        if node is None:
            pytest.skip("node is absent, so design/build.mjs cannot be run here")
        py, mjs = tmp_path / "py", tmp_path / "mjs"
        assert self.run(["python3", str(BUILD_PY)], py).returncode == 0
        assert self.run([node, str(BUILD_MJS)], mjs).returncode == 0
        assert self.files(py) == self.files(mjs)

    def test_the_canvas_reserves_a_slot_for_every_captured_screen(self, tmp_path):
        self.run(["python3", str(BUILD_PY)], tmp_path)
        laid_out = {board["file"] for board in json.loads((tmp_path / "canvas.json").read_text())["artboards"]}
        for screen in json.loads(text(SCREENS))["screens"]:
            assert f"{screen['name']}.dc.html" in laid_out

    def test_a_generated_artboard_carries_its_own_stamp(self, tmp_path):
        """No route, no commit, no clock. This file is the reference, and the digest is what a duplicate compares."""
        self.run(["python3", str(BUILD_PY)], tmp_path)
        body = (tmp_path / "Palette.dc.html").read_text(encoding="utf-8")
        for field in ("by", "viewport", "digest"):
            assert f"data-generated-{field}=" in body
        assert "data-generated-at=" not in body
        assert "data-generated-commit=" not in body

    def test_every_grey_is_spelled_once(self):
        """A hex written twice is what step 3's one generator exists to prevent."""
        body = text(BUILD_PY)
        table = body[body.index("GREYS = [") : body.index("GREY = {")]
        for grey in re.findall(r"#[0-9a-f]{6}", table):
            assert body.count(grey) == 1, f"{grey} is spelled more than once"

    def test_neither_copy_writes_a_name_the_capture_owns(self):
        for generator in (BUILD_PY, BUILD_MJS):
            assert "the capture owns" in text(generator)

    def test_this_repository_keeps_no_generated_artboard(self):
        """A generated file under `design/` here would be seeded into every project.

        `seeds.json` expands `design/` over whatever is on disk, so an artboard
        written by a run in this checkout would land in a project and collide
        with that project's own next run.
        """
        for pack in ("python", "typescript"):
            seeded = {rel for rel, _ in adopt.seeds(ROOT, pack)}
            assert not [r for r in seeded if r.endswith((".dc.html", ".classes.html", "canvas.json"))]

    def test_this_repository_ignores_a_generated_artboard(self):
        """The guard before the one above. `seeds.json` expands over the disk, so an
        artboard that never reaches the index is still seeded, and the ignore is what
        keeps a run in this checkout from putting one there (#89).
        """
        here = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "design/Home.dc.html", "design/Home.classes.html"],
            capture_output=True,
            text=True,
        )
        assert here.returncode == 0, here.stdout
        kept = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "design/build.py", "design/screens.json"],
            capture_output=True,
            text=True,
        )
        assert kept.returncode == 1, kept.stdout
