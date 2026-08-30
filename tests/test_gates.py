"""Rule 17's declaration, the runner that reads it, and what a project inherits.

Nothing here asserts which gates this repository declares. A suite restating
the list would be the second copy of the thing the declaration exists to
remove. What is asserted is that the file is well formed, that `bin/verify`
reports a failing gate instead of passing over it, and that a project seeded by
`adopt` receives a runner it can actually run.

`bin/verify --root` and `bin/check-style <path>` both point at a fixture, which
keeps this suite from failing every time a real gate changes.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / ".agentkit" / "gates.toml"
VERIFY = ROOT / "bin" / "verify"
CHECK_STYLE = ROOT / "bin" / "check-style"
CHECK_PROBES = ROOT / "bin" / "check-probes"

DECLARED = tomllib.loads(GATES.read_text(encoding="utf-8"))["gate"]

# The executables a project inherits. `bin/adopt` is this template's own tool
# and is deliberately absent.
SEEDED_BIN = (
    "bin/verify",
    "bin/check-style",
    "bin/check-probes",
    "bin/check-process",
    "bin/surface",
)


def load(path: Path):
    """Import an extensionless executable, which cannot be imported by name."""
    loader = SourceFileLoader(path.name.replace("-", "_"), str(path))
    module = module_from_spec(spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True, cwd=ROOT
    )


def git_repo(path: Path, files: dict[str, str]) -> Path:
    """A real repository, because both checkers find their files through git."""
    path.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    return path


class TestDeclaration:
    @pytest.mark.parametrize("gate", DECLARED, ids=lambda g: g["name"])
    def test_a_gate_declares_a_name_and_a_command(self, gate):
        assert gate.get("name")
        assert gate.get("command")

    def test_gate_names_are_unique(self):
        names = [g["name"] for g in DECLARED]
        assert len(names) == len(set(names)), names

    def test_no_gate_carries_a_field_that_would_let_it_not_fail(self):
        """A gate that cannot fail defeats rule 17, so the schema has no such field."""
        allowed = {"name", "command", "cwd"}
        for gate in DECLARED:
            assert set(gate) <= allowed, f"{gate['name']} declares {set(gate) - allowed}"

    def test_every_directory_holding_python_is_named_by_a_gate(self):
        """A directory no command names is checked by nothing, which is where `design/` sat.

        The assertion is a property. Which gates are declared stays the
        declaration's business, and a new directory of python joins one of the
        commands or fails here.
        """
        tracked = subprocess.run(
            ["git", "ls-files", "*.py"], capture_output=True, text=True, cwd=ROOT
        ).stdout.split()
        holding = {Path(rel).parts[0] for rel in tracked if "/" in rel}
        named = {
            part
            for gate in DECLARED
            for word in gate["command"].split()
            for part in Path(word).parts
        }
        assert holding <= named, sorted(holding - named)

    def test_no_tracked_prose_restates_a_gate_command(self):
        """Rule 17 names this file and no command."""
        tracked = subprocess.run(
            ["git", "ls-files", "*.md", "*.yml", "*.yaml"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        ).stdout.split()
        commands = [g["command"] for g in DECLARED]
        offenders = [
            f"{name}: {c}"
            for name in tracked
            for c in commands
            if c in (ROOT / name).read_text(encoding="utf-8", errors="ignore")
        ]
        assert not offenders, offenders


class TestRunner:
    def test_it_lists_what_is_declared(self):
        done = run(VERIFY, "--list")
        assert done.returncode == 0
        for gate in DECLARED:
            assert gate["name"] in done.stdout

    def test_it_refuses_a_gate_that_is_not_declared(self):
        done = run(VERIFY, "no-such-gate")
        assert done.returncode != 0
        assert "no-such-gate" in done.stderr + done.stdout

    def test_a_missing_declaration_is_an_error(self, tmp_path):
        done = run(VERIFY, "--root", str(tmp_path), "--list")
        assert done.returncode != 0
        assert "No gate declaration" in done.stderr + done.stdout

    def test_an_empty_declaration_is_a_choice_and_passes(self, tmp_path):
        """A project may delete every gate it was seeded, so this may not be an error."""
        (tmp_path / ".agentkit").mkdir()
        (tmp_path / ".agentkit" / "gates.toml").write_text("# nothing yet\n", encoding="utf-8")
        done = run(VERIFY, "--root", str(tmp_path))
        assert done.returncode == 0
        assert "declares no gates" in done.stdout

    def test_every_gate_runs_even_after_one_fails(self, tmp_path):
        """Stopping at the first failure hides the second thing wrong with the tree."""
        (tmp_path / ".agentkit").mkdir()
        (tmp_path / ".agentkit" / "gates.toml").write_text(
            '[[gate]]\nname = "first"\ncommand = "python3 -c \'pass\'"\n'
            '[[gate]]\nname = "broken"\ncommand = "python3 -c \'raise SystemExit(3)\'"\n'
            '[[gate]]\nname = "last"\ncommand = "python3 -c \'pass\'"\n',
            encoding="utf-8",
        )
        done = run(VERIFY, "--root", str(tmp_path))
        assert done.returncode == 1
        assert "1 of 3 gate(s) failed: broken" in done.stdout
        assert done.stdout.count("pass  ") == 2

    def test_a_command_that_is_not_installed_fails_rather_than_raises(self, tmp_path):
        (tmp_path / ".agentkit").mkdir()
        (tmp_path / ".agentkit" / "gates.toml").write_text(
            '[[gate]]\nname = "missing"\ncommand = "no-such-executable --version"\n',
            encoding="utf-8",
        )
        done = run(VERIFY, "--root", str(tmp_path))
        assert done.returncode == 1
        assert "FAIL" in done.stdout


class TestCheckers:
    def test_check_style_reads_the_directory_it_is_given(self, tmp_path):
        """One copy gates several repositories. A template needs that."""
        repo = git_repo(tmp_path / "other", {"a.md": "A sentence with " + chr(8212) + ".\n"})
        done = run(CHECK_STYLE, str(repo))
        assert done.returncode == 1
        assert "a.md:1" in done.stdout
        assert "em dash" in done.stdout

    def test_check_style_reads_a_single_file(self, tmp_path):
        """Rule 24 covers a report or a handover, which live outside any repository."""
        report = tmp_path / "handover.md"
        report.write_text("A sentence with " + chr(8212) + ".\n", encoding="utf-8")
        done = run(CHECK_STYLE, str(report))
        assert done.returncode == 1
        assert "handover.md:1" in done.stdout
        assert "em dash" in done.stdout

    def test_a_clean_single_file_passes(self, tmp_path):
        report = tmp_path / "handover.md"
        report.write_text("A sentence with nothing wrong with it.\n", encoding="utf-8")
        done = run(CHECK_STYLE, str(report))
        assert done.returncode == 0
        assert "Style is clean." in done.stdout

    def test_changed_against_a_single_file_says_what_to_pass(self, tmp_path):
        """`--changed` asks git for a diff, and a lone file has no repository to diff against."""
        report = tmp_path / "handover.md"
        report.write_text("Prose.\n", encoding="utf-8")
        done = run(CHECK_STYLE, str(report), "--changed")
        assert done.returncode != 0
        assert "Give it a directory" in done.stderr + done.stdout

    def test_a_path_that_is_neither_says_so(self, tmp_path):
        done = run(CHECK_STYLE, str(tmp_path / "nothing.md"))
        assert done.returncode != 0
        assert "neither a file nor a directory" in done.stderr + done.stdout

    def test_a_check_date_in_a_skill_description_fails(self, tmp_path):
        """#45 measured what a date with no gate behind it buys: four refreshes due, zero run.

        The body line is left alone. A date beside a number says when that
        number was read, and a checker cannot tell that from a freshness claim.
        """
        skill = (
            "---\n"
            "name: dated\n"
            "description: What it does. Use when X. Sources checked 2026-08-28.\n"
            "---\n"
            "\n"
            "A number read from a named source on 2026-08-28.\n"
        )
        repo = git_repo(tmp_path / "dated", {".claude/skills/dated/SKILL.md": skill})
        done = run(CHECK_STYLE, str(repo))
        assert done.returncode == 1
        assert "SKILL.md:3" in done.stdout
        assert "check date in a description" in done.stdout
        assert "SKILL.md:6" not in done.stdout

    def test_an_extensionless_executable_is_in_scope(self, tmp_path):
        """Matching on suffix alone let bin/adopt through its own style gate."""
        style = load(CHECK_STYLE)
        repo = git_repo(
            tmp_path / "scripts",
            {
                "runner": "#!/usr/bin/env python3\nprint('hi')\n",
                "LICENSE": "Copyright, and no shebang.\n",
                "notes.md": "Prose.\n",
            },
        )
        assert sorted(p.name for p in style.tracked(repo, False)) == ["notes.md", "runner"]

    def test_a_probe_that_cannot_import_fails(self, tmp_path):
        probes = tmp_path / "probes"
        probes.mkdir()
        (probes / "needs_project.py").write_text("import no_such_module_here\n", encoding="utf-8")
        done = run(CHECK_PROBES, str(probes))
        assert done.returncode == 1
        assert "needs_project.py" in done.stdout

    def test_a_probe_that_does_not_parse_fails(self, tmp_path):
        probes = tmp_path / "probes"
        probes.mkdir()
        (probes / "broken.py").write_text("def (\n", encoding="utf-8")
        done = run(CHECK_PROBES, str(probes))
        assert done.returncode == 1
        assert "does not parse" in done.stdout

    def test_an_empty_probes_directory_passes(self, tmp_path):
        """Rule 9 applies where there is an external interface. A project with none has no probes."""
        probes = tmp_path / "probes"
        probes.mkdir()
        done = run(CHECK_PROBES, str(probes))
        assert done.returncode == 0

    def test_the_probe_interpreter_is_never_the_virtualenv(self):
        """`-I` does not exclude a venv's own site-packages, so the interpreter is the isolation.

        Under `.venv/bin/python3` a probe importing the project succeeds, which
        is the exact failure rule 9's gate exists to catch.
        """
        probes = load(CHECK_PROBES)
        chosen = probes.bare_interpreter()
        if sys.prefix == sys.base_prefix:
            assert chosen == sys.executable
        else:
            assert not chosen.startswith(sys.prefix), chosen
            assert chosen.startswith(sys.base_prefix), chosen

    def test_a_probes_directory_that_is_not_there_says_what_to_do(self, tmp_path):
        done = run(CHECK_PROBES, str(tmp_path / "nothing"))
        assert done.returncode != 0
        assert "Drop the probes gate" in done.stderr + done.stdout


class TestWhatAProjectInherits:
    """The half nothing checked before, and the half that let the two repos diverge."""

    def test_the_runner_and_the_checkers_are_seeded(self):
        tracked = __import__("json").loads((ROOT / "seeds.json").read_text())["tracked"]
        for rel in SEEDED_BIN:
            assert rel in tracked, f"{rel} is not seeded, so a project cannot run its gates"

    def test_adopt_is_not_seeded(self):
        """The template's own tool does not belong in a project it seeded."""
        tracked = __import__("json").loads((ROOT / "seeds.json").read_text())["tracked"]
        assert "bin/adopt" not in tracked
        assert "bin/" not in tracked

    @pytest.mark.parametrize("rel", SEEDED_BIN)
    def test_a_seeded_executable_stays_executable(self, rel):
        """write_bytes drops the mode, and gates.toml names these as `bin/x`."""
        assert (ROOT / rel).stat().st_mode & 0o111, f"{rel} is not executable here"

    def test_every_pack_names_a_command_the_project_will_have(self):
        """A gate naming a command the project cannot run is the failure PACKS warns about."""
        adopt = load(ROOT / "bin" / "adopt")
        for pack, gates in adopt.PACKS.items():
            for name, command, _ in gates:
                first = command.split()[0]
                if first.startswith("bin/"):
                    assert first in SEEDED_BIN, f"{pack}/{name} names unseeded {first}"

    def test_the_loop_is_seeded(self):
        """A project gets /work, or it has no way to ask what to do next."""
        tracked = __import__("json").loads((ROOT / "seeds.json").read_text())["tracked"]
        assert ".claude/skills/" in tracked
        assert ".claude/commands/" in tracked
        assert (ROOT / ".claude" / "skills" / "pick-work" / "SKILL.md").is_file()
        assert (ROOT / ".claude" / "commands" / "work.md").is_file()

    def test_pick_work_carries_no_other_project_taxonomy(self):
        """It reads `gh label list` so one project's labels stay in that project."""
        skill = (ROOT / ".claude" / "skills" / "pick-work" / "SKILL.md").read_text()
        assert "gh label list" in skill
        for borrowed in ("aw-server", "sessionizer", "mac-hours", "area: pipeline"):
            assert borrowed not in skill, f"pick-work names {borrowed}"

    def test_no_seeded_command_needs_a_shell(self):
        """The runner uses shlex and no shell, so `cd x && y` looks for a binary named cd."""
        adopt = load(ROOT / "bin" / "adopt")
        for pack, gates in adopt.PACKS.items():
            for name, command, _ in gates:
                assert "&&" not in command and not command.startswith("cd "), f"{pack}/{name}"


class TestWhatCIRuns:
    """The workflow, here and in a project `adopt` seeds.

    A step per gate is a second copy of the gate list. The copy this repository
    kept made the file unseedable: every step read `bin/verify <name>` with
    names no other project declares, and a seeded copy died on step two with
    `No gate named probes`.
    """

    GATES_YML = ROOT / ".github" / "workflows" / "gates.yml"

    def test_the_workflow_names_no_gate(self):
        body = self.GATES_YML.read_text(encoding="utf-8")
        for gate in DECLARED:
            assert f"bin/verify {gate['name']}" not in body, gate["name"]

    def test_the_workflow_runs_the_runner(self):
        assert "- run: bin/verify\n" in self.GATES_YML.read_text(encoding="utf-8")

    def test_the_seeded_workflow_agrees_with_this_one(self):
        """Both files run a bare `bin/verify`, so neither holds a gate name."""
        adopt = load(ROOT / "bin" / "adopt")
        seeded = adopt.gates_workflow("python")
        assert "      - run: bin/verify\n" in seeded
        assert "      - run: bin/verify\n" in self.GATES_YML.read_text(encoding="utf-8")

    def test_no_workflow_is_a_seeded_byte_copy(self):
        """A replaced workflow leaves the project's edit in a `.local` GitHub never runs."""
        tracked = __import__("json").loads((ROOT / "seeds.json").read_text())["tracked"]
        assert not [t for t in tracked if t.startswith(".github")]

    def test_the_runner_writes_its_table_to_the_job_summary(self, tmp_path):
        """One step names no gate, so the summary is where a failing gate names itself."""
        (tmp_path / ".agentkit").mkdir()
        (tmp_path / ".agentkit" / "gates.toml").write_text(
            '[[gate]]\nname = "ok"\ncommand = "python3 -c \'pass\'"\n'
            '[[gate]]\nname = "broken"\ncommand = "python3 -c \'raise SystemExit(3)\'"\n',
            encoding="utf-8",
        )
        summary = tmp_path / "summary.md"
        done = subprocess.run(
            [sys.executable, str(VERIFY), "--root", str(tmp_path)],
            capture_output=True,
            text=True,
            cwd=ROOT,
            env={**os.environ, "GITHUB_STEP_SUMMARY": str(summary)},
        )
        assert done.returncode == 1
        written = summary.read_text(encoding="utf-8")
        assert "broken" in written
        assert "1 of 2 gate(s) failed" in written

    def test_the_summary_is_written_nowhere_outside_actions(self, tmp_path):
        (tmp_path / ".agentkit").mkdir()
        (tmp_path / ".agentkit" / "gates.toml").write_text(
            '[[gate]]\nname = "ok"\ncommand = "python3 -c \'pass\'"\n', encoding="utf-8"
        )
        env = {k: v for k, v in os.environ.items() if k != "GITHUB_STEP_SUMMARY"}
        done = subprocess.run(
            [sys.executable, str(VERIFY), "--root", str(tmp_path)],
            capture_output=True,
            text=True,
            cwd=ROOT,
            env=env,
        )
        assert done.returncode == 0
        assert "1 gate(s) passed." in done.stdout
