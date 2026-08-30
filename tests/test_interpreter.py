"""The interpreter the `bin/` executables run on, and the floor they hold to.

Two shebangs live in `bin/`. `bin/verify` and `bin/check-process` ask uv for an
interpreter, so the machine's own Python is never theirs. The rest carry
`#!/usr/bin/env python3` and run on whatever is on `PATH`, which on a stock
macOS is 3.9.6 with no pyenv and no uv.

#111 is what that costs when it goes wrong. `bin/adopt` imported
`datetime.UTC`, added in 3.11, and the first command the README tells a new
adopter to run ended in a traceback from inside a file they had never opened,
with nothing in the error naming a Python version.

What is asserted here is a floor rather than a version. A project cloning this
repository runs `bin/adopt` before it has installed anything at all, which is
the same argument rule 9 makes for a probe.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"

# The floor for anything carrying `#!/usr/bin/env python3`. macOS has shipped
# 3.9 since Monterey and it is the oldest interpreter a new adopter is likely
# to meet.
FLOOR = (3, 9)

UV_SHEBANG = "uv run --script"

# Stdlib names added after the floor. A sampler and not a proof: `ast` sees an
# import and cannot see an attribute resolved at runtime, so this catches the
# shape #111 actually took, `from datetime import UTC`, and the neighbours
# somebody would reach for next. The dynamic test below is the real check, and
# it only runs where an old interpreter exists.
ADDED_AFTER_FLOOR = {
    "datetime": {"UTC"},
    "typing": {"Self", "Never", "LiteralString", "assert_never", "assert_type"},
    "enum": {"StrEnum", "ReprEnum"},
    "asyncio": {"TaskGroup", "timeout"},
    "itertools": {"batched"},
    "tomllib": {"load", "loads"},
}


def bare_interpreter_scripts() -> list[Path]:
    """Every `bin/` entry that runs on the machine's own Python."""
    found = []
    for path in sorted(BIN.iterdir()):
        if not path.is_file():
            continue
        first = path.read_text(encoding="utf-8", errors="replace").split("\n", 1)[0]
        if first.startswith("#!") and UV_SHEBANG not in first:
            found.append(path)
    return found


def older_interpreter() -> str | None:
    """A real interpreter older than the floor, when the machine has one.

    `/usr/bin/python3` on macOS is the one an adopter actually hits. There is
    no equivalent on a CI runner, so the dynamic test skips there and the
    static one carries the check.
    """
    stock = Path("/usr/bin/python3")
    if not stock.exists():
        return None
    done = subprocess.run(
        [str(stock), "-c", "import sys; print(sys.version_info[:2])"],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        return None
    major, minor = ast.literal_eval(done.stdout.strip())
    return str(stock) if (major, minor) < sys.version_info[:2] else None


class TestTheBareInterpreterFloor:
    """`#!/usr/bin/env python3` means whatever the machine has, so this holds."""

    def test_some_script_runs_on_the_machines_own_python(self):
        """A guard on the guard: if every shebang moved to uv, the rest asserts nothing."""
        assert bare_interpreter_scripts()

    def test_adopt_is_one_of_them(self):
        """#111 is only interesting because `bin/adopt` runs before uv is a given."""
        assert BIN / "adopt" in bare_interpreter_scripts()

    @pytest.mark.parametrize("script", bare_interpreter_scripts(), ids=lambda p: p.name)
    def test_no_import_added_after_the_floor(self, script):
        """The shape #111 took: `from datetime import UTC` on a 3.9 machine."""
        tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            too_new = ADDED_AFTER_FLOOR.get(node.module, set())
            imported = {alias.name for alias in node.names}
            offending = imported & too_new
            assert not offending, (
                f"{script.name}:{node.lineno} imports {sorted(offending)} from "
                f"{node.module}, added after Python {'.'.join(map(str, FLOOR))}. "
                f"{script.name} carries a bare python3 shebang, so it runs on "
                f"whatever the machine has."
            )

    @pytest.mark.parametrize("script", bare_interpreter_scripts(), ids=lambda p: p.name)
    def test_it_answers_on_an_older_interpreter(self, script):
        """The real check, where the machine has an interpreter to run it on.

        Skipped on a runner whose only python3 is current, which is every CI
        runner this repository uses. The static test above is what covers it
        there.
        """
        old = older_interpreter()
        if old is None:
            pytest.skip("no interpreter older than this one on the machine")
        done = subprocess.run(
            [old, str(script), "--help"], capture_output=True, text=True, cwd=ROOT
        )
        assert "Error" not in done.stderr, f"{script.name} under {old}: {done.stderr.strip()[:300]}"
