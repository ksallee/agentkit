"""The design directory a project is seeded with.

Nothing here launches a browser. `probes/design_capture.py` does that, and
`bin/check-probes` runs its `--help` on every gate run. What is left is the
half that can drift silently: two drivers, one contract, and a probe asserting
a stamp all three have to spell the same way.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "design"
CONTRACT = DESIGN / "capture.js"
SCREENS = DESIGN / "screens.json"
DRIVERS = (DESIGN / "capture.py", DESIGN / "capture.mjs")
PROBE = ROOT / "probes" / "design_capture.py"

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
