"""Seeding a template tree into a project, and updating it later.

Every test runs against `tests/fixtures/template/`, which carries a seed list
of its own. A suite pointed at this repository's real files would fail every
time a template file changed, and the mechanism under test has nothing to do
with which files the template happens to hold.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tomllib
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "template"

# `bin/adopt` carries no extension, because it is run rather than imported
# everywhere except here.
_loader = SourceFileLoader("adopt", str(ROOT / "bin" / "adopt"))
_spec = importlib.util.spec_from_loader("adopt", _loader)
adopt = importlib.util.module_from_spec(_spec)
# Registered before it runs, because `@dataclass` resolves annotations through
# `sys.modules[cls.__module__]` and a module absent from there raises.
sys.modules["adopt"] = adopt
_loader.exec_module(adopt)

# The seven answers, as `main` assembles them. One constant, because the router
# and the team layer are rendered from the same dict. `surface` is empty here
# because `main` passes that when nobody answered `--surface`, and the
# team layer says so in place of a value.
ANSWERS = {
    "pack": "python",
    "name": "demo",
    "summary": "A project.",
    "phase": "building",
    "merge": "Both of us review.",
    "surface": "",
    "runner": "cloud",
}

SKILL = ".claude/skills/demo/SKILL.md"
STYLE = "docs/development/STYLE.md"
ALL_SEEDED = (".claude/skills/demo/SKILL.md", ".claude/skills/demo/reference.md", STYLE)


@pytest.fixture
def project(tmp_path):
    """An empty project directory, with no manifest and no scaffolding."""
    p = tmp_path / "project"
    p.mkdir()
    return p


@pytest.fixture
def template(tmp_path):
    """A writable copy of the fixture tree, so a test can change it upstream."""
    import shutil

    p = tmp_path / "template"
    shutil.copytree(FIXTURE, p)
    return p


def statuses(rows):
    return {row.rel: row.status for row in rows}


class TestTheSeedList:
    def test_a_directory_entry_carries_every_file_under_it(self):
        rels = [rel for rel, _ in adopt.seeds(FIXTURE)]
        assert rels == sorted(ALL_SEEDED)

    def test_a_missing_entry_stops_the_run(self, template):
        (template / "seeds.json").write_text(json.dumps({"tracked": ["docs/GONE.md"]}))
        with pytest.raises(SystemExit) as raised:
            adopt.seeds(template)
        assert "docs/GONE.md" in str(raised.value)

    def test_a_directory_entry_naming_a_file_stops_the_run(self, template):
        (template / "seeds.json").write_text(json.dumps({"tracked": ["docs/development/STYLE.md/"]}))
        with pytest.raises(SystemExit):
            adopt.seeds(template)

    def test_compiled_python_never_seeds(self, template):
        (template / ".claude" / "skills" / "demo" / "stale.pyc").write_bytes(b"\x00")
        assert "stale" not in " ".join(rel for rel, _ in adopt.seeds(template))


class TestTheTemplatesOwnTools:
    """`template_only`, the second list: real files a directory entry expands over.

    `.claude/skills/` and `.claude/commands/` are directory entries, so the
    `adopt` skill and the `/agentkit` command reached every project by
    expansion and offered it a `bin/adopt` that `seeds.json` withholds. Naming
    every other skill one by one instead drops a skill from every project the
    moment somebody adds one here.
    """

    @staticmethod
    def declare(template, tracked, withheld):
        (template / "seeds.json").write_text(json.dumps({"tracked": tracked, "template_only": withheld}))
        return {rel for rel, _ in adopt.seeds(template)}

    def test_a_withheld_directory_seeds_none_of_its_files(self, template):
        assert self.declare(template, [".claude/skills/"], [".claude/skills/demo/"]) == set()

    def test_a_withheld_file_is_the_only_one_dropped(self, template):
        rels = self.declare(template, [".claude/skills/"], [".claude/skills/demo/reference.md"])
        assert rels == {SKILL}

    def test_an_entry_tracked_by_name_seeds_anyway(self, template):
        """A path somebody typed into `tracked` is a decision, and it wins."""
        rels = self.declare(template, [STYLE], [STYLE])
        assert rels == {STYLE}

    def test_an_exclusion_naming_nothing_stops_the_run(self, template):
        """A stale exclusion silently stops excluding, which is the failure to catch."""
        with pytest.raises(SystemExit) as raised:
            self.declare(template, [STYLE], ["docs/GONE.md"])
        assert "docs/GONE.md" in str(raised.value)

    def test_an_absent_list_leaves_every_expansion_alone(self, template):
        (template / "seeds.json").write_text(json.dumps({"tracked": [".claude/skills/"]}))
        assert {rel for rel, _ in adopt.seeds(template)} == {SKILL, SKILL.replace("SKILL.md", "reference.md")}

    def test_this_repository_withholds_the_adopt_skill_and_its_command(self):
        """The live defect: a project got a skill driving a tool it does not have."""
        seeded = {rel for rel, _ in adopt.seeds(ROOT)}
        assert ".claude/skills/adopt/SKILL.md" not in seeded
        assert ".claude/commands/agentkit.md" not in seeded

    def test_this_repository_still_seeds_the_rest_of_both_directories(self):
        seeded = {rel for rel, _ in adopt.seeds(ROOT)}
        assert ".claude/commands/work.md" in seeded
        assert ".claude/skills/pick-work/SKILL.md" in seeded

    def test_the_note_explains_the_list(self):
        """`seeds.json` is read by somebody deciding what a project should get."""
        declared = json.loads((ROOT / "seeds.json").read_text())
        assert "template_only" in declared["note"]


class TestThePacksOwnDriver:
    """`per_pack`, the third list: one file per language pack, chosen at adoption.

    A capture reads computed styles out of a real browser, so it needs a driver,
    and the driver a project can install is the one its pack already declares.
    The template holds both and a project receives one.
    """

    @staticmethod
    def declare(template, tracked, per_pack, pack):
        (template / "seeds.json").write_text(json.dumps({"tracked": tracked, "per_pack": per_pack}))
        return {rel for rel, _ in adopt.seeds(template, pack)}

    def test_only_the_chosen_packs_file_seeds(self, template):
        per_pack = {"python": [STYLE], "none": []}
        assert self.declare(template, [".claude/skills/"], per_pack, "python") == {STYLE, SKILL, SKILL.replace("SKILL.md", "reference.md")}

    def test_another_packs_file_is_withheld_from_the_expansion(self, template):
        per_pack = {"python": [STYLE], "none": []}
        seeded = self.declare(template, [".claude/skills/", "docs/development/"], per_pack, "none")
        assert STYLE not in seeded

    def test_a_pack_the_list_does_not_name_stops_the_run(self, template):
        with pytest.raises(SystemExit) as raised:
            self.declare(template, [STYLE], {"python": []}, "typescript")
        assert "typescript" in str(raised.value)

    def test_an_absent_list_leaves_every_pack_alone(self, template):
        (template / "seeds.json").write_text(json.dumps({"tracked": [STYLE]}))
        assert {rel for rel, _ in adopt.seeds(template, "typescript")} == {STYLE}

    def test_every_pack_this_repository_declares_has_a_driver_list(self):
        """A pack with no entry raises at adoption, which is a defect nobody sees until then."""
        declared = json.loads((ROOT / "seeds.json").read_text())
        assert set(declared["per_pack"]) == set(adopt.PACKS)

    DRIVERS = {"design/capture.py", "design/capture.mjs"}
    GENERATORS = {"design/build.py", "design/build.mjs"}

    def test_a_language_pack_seeds_one_driver(self):
        """A python project gains nothing from a node driver it will not run."""
        for pack in adopt.PACKS:
            if pack == "none":
                continue
            seeded = {rel for rel, _ in adopt.seeds(ROOT, pack)} & self.DRIVERS
            assert len(seeded) == 1, pack

    def test_the_none_pack_seeds_both_drivers_and_both_generators(self):
        """#142. A driver needs a browser, and a gate list naming no toolchain says
        nothing about which runtime the machine has, so the pack that declares no
        language takes the pair and `design-process` step 6 runs whichever is there.
        """
        seeded = {rel for rel, _ in adopt.seeds(ROOT, "none")}
        assert seeded >= self.DRIVERS
        assert seeded >= self.GENERATORS

    def test_the_note_says_the_none_pack_takes_both(self):
        declared = json.loads((ROOT / "seeds.json").read_text())
        assert "none takes both pairs" in declared["note"]

    def test_the_contract_and_the_screen_list_seed_to_every_pack(self):
        for pack in adopt.PACKS:
            seeded = {rel for rel, _ in adopt.seeds(ROOT, pack)}
            assert {"design/capture.js", "design/screens.json"} <= seeded

    def test_the_note_explains_the_list(self):
        declared = json.loads((ROOT / "seeds.json").read_text())
        assert "per_pack" in declared["note"]


class TestWhatEveryPackGates:
    """The two gates that name no language toolchain, and the pack that declared neither.

    `none` declared nothing, so a project on it took `bin/check-style`, rule 24
    and a workflow running `bin/verify`, and `bin/verify` printed a green table
    over a tree nothing checked (#141).
    """

    def test_every_pack_declares_the_style_gate(self):
        for pack in adopt.PACKS:
            commands = {command for _, command, _ in adopt.PACKS[pack]}
            assert "bin/check-style ." in commands, pack

    def test_no_pack_declares_an_empty_list(self):
        """`run_gates` special-cases no pack, and no adoption seeds a list nothing runs."""
        for pack in adopt.PACKS:
            assert adopt.PACKS[pack], pack

    def test_the_none_pack_declares_those_two_and_no_third(self):
        assert [name for name, _, _ in adopt.PACKS["none"]] == ["style", "probes"]


class TestTheSeededProbe:
    """`probes/skill_sources.py`, the one file under `probes/` named on its own line.

    It reads whatever `.claude/skills/` holds in the repository it runs in, so
    a project that took the skills can check the URLs they cite. Every other
    probe here reads an interface a seeded project may never have, and rule 9
    asks a project to drop a rule it has no interface for.
    """

    def test_the_url_probe_seeds(self):
        assert "probes/skill_sources.py" in {rel for rel, _ in adopt.seeds(ROOT)}

    def test_no_other_file_under_probes_seeds(self):
        """A `/` typed onto that entry would carry five probes nobody asked for."""
        others = {p.relative_to(ROOT).as_posix() for p in (ROOT / "probes").iterdir() if p.is_file()}
        others -= {"probes/skill_sources.py"}
        assert others, "probes/ holds nothing else, so this asserts nothing"
        for pack in adopt.PACKS:
            assert not others & {rel for rel, _ in adopt.seeds(ROOT, pack)}, pack

    def test_the_note_explains_the_one_entry(self):
        declared = json.loads((ROOT / "seeds.json").read_text())
        assert "probes/skill_sources.py" in declared["note"]

    def test_every_seeded_file_citing_an_unseeded_probe_names_the_checkout(self):
        """#159. A citation a project cannot follow is a path to a file it does not have.

        #124 settled the wording: name the agentkit checkout, and say the probe
        is seeded nowhere, so a reader knows the result travels and the probe
        does not. That fix went into one markdown file and left the same
        sentence in `bin/check-process`, which every project also receives.
        Reading every seeded file rather than the markdown catches the second.
        """
        cited = re.compile(r"probes/[a-z0-9_]+\.py")
        offenders = []
        for pack in adopt.PACKS:
            for rel, path in adopt.seeds(ROOT, pack):
                seeded = {r for r, _ in adopt.seeds(ROOT, pack)}
                try:
                    lines = path.read_text(encoding="utf-8").splitlines()
                except (UnicodeDecodeError, OSError):
                    continue
                for n, line in enumerate(lines):
                    for probe in cited.findall(line):
                        if probe in seeded:
                            continue
                        # Normalised, because a citation wraps and the phrase
                        # then carries the next line's indentation in the middle.
                        window = " ".join(" ".join(lines[max(0, n - 2) : n + 3]).split())
                        if "agentkit checkout" not in window:
                            offenders.append(f"{pack}: {rel}:{n + 1} cites {probe}")
        assert not offenders, "\n".join(sorted(set(offenders)))

    def test_every_pack_gates_the_probe(self):
        """A seeded probe nothing runs is rule 9's dead rule with a file attached.

        `seeds.json` puts `probes/skill_sources.py` in `tracked`, so every pack
        receives a probe, and a pack gating none of it carries rule 9 with
        nothing behind it. `typescript` was the one pack left out, on the
        grounds that a node project should not take a Python interpreter for
        one gate, and it already takes two (#124).
        """
        for pack in adopt.PACKS:
            commands = {command for _, command, _ in adopt.PACKS[pack]}
            assert "bin/check-probes" in commands, pack
            assert "probes/skill_sources.py" in {rel for rel, _ in adopt.seeds(ROOT, pack)}, pack

    def test_the_interpreter_was_paid_before_the_probe_gate_was_considered(self):
        """The measurement #124 settled on, kept where a reader of the gate list is.

        Both checkers a pack declares before this one run under python3, so the
        argument that the probes gate costs a node project an interpreter
        cannot separate it from the style gate every pack already has.
        """
        for checker in ("bin/check-style", "bin/check-probes", "bin/adopt"):
            assert (ROOT / checker).read_text().splitlines()[0] == "#!/usr/bin/env python3"


class TestTheSeededTest:
    """One scaffolding test per language, seeded to the packs that run it.

    A project's `test` gate exits non-zero when it collects nothing, so a
    project with no test directory failed a gate of its own on the day it was
    adopted: `uv run pytest` on #108, `pnpm test` on #112. Each seeded file
    asserts what an adopted project has, so the green says the scaffolding is
    sound.
    """

    def test_the_python_packs_take_the_pytest_file(self):
        for pack in ("python", "python+typescript"):
            assert "tests/test_scaffolding.py" in {rel for rel, _ in adopt.seeds(ROOT, pack)}, pack

    def test_the_typescript_pack_takes_the_node_file_and_no_pytest_file(self):
        seeded = {rel for rel, _ in adopt.seeds(ROOT, "typescript")}
        assert "tests/scaffolding.test.mjs" in seeded
        assert "tests/test_scaffolding.py" not in seeded

    def test_the_both_pack_takes_the_node_file_under_web(self):
        """The pnpm gates run in `web/`, and a root `package.json` answers for nothing."""
        seeded = {rel for rel, _ in adopt.seeds(ROOT, "python+typescript")}
        assert "web/tests/scaffolding.test.mjs" in seeded
        assert "tests/scaffolding.test.mjs" not in seeded

    def test_the_none_pack_takes_neither(self):
        seeded = {rel for rel, _ in adopt.seeds(ROOT, "none")}
        assert not seeded & {"tests/test_scaffolding.py", "tests/scaffolding.test.mjs"}

    def test_no_other_file_under_tests_seeds(self):
        """A `/` typed onto either entry would carry this repository's own suite.

        `tests/test_adopt.py` reads `bin/adopt`, which no project has, so every
        sibling of the two seeded files fails in the first project that took it.
        """
        others = {
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "tests").rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }
        others -= {"tests/test_scaffolding.py", "tests/scaffolding.test.mjs"}
        assert "tests/test_adopt.py" in others, "this asserts nothing without a sibling"
        for pack in adopt.PACKS:
            landed = {rel for rel, _ in adopt.seeds(ROOT, pack)}
            sources = {src.relative_to(ROOT).as_posix() for _, src in adopt.seeds(ROOT, pack)}
            assert not others & (landed | sources), pack

    def test_the_note_explains_both_entries(self):
        declared = json.loads((ROOT / "seeds.json").read_text())
        assert "tests/test_scaffolding.py" in declared["note"]
        assert "tests/scaffolding.test.mjs" in declared["note"]

    def test_each_pack_declares_the_gate_that_runs_its_file(self):
        wanted = {
            "python": "uv run pytest",
            "typescript": "pnpm test",
            "python+typescript": "pnpm test",
        }
        for pack, command in wanted.items():
            commands = {declared for _, declared, _ in adopt.PACKS[pack]}
            assert command in commands, pack


class TestTheSeededLintConfig:
    """`ruff.toml`, seeded to the packs that declare a command reading it.

    `uvx ruff check .` with no config in reach runs under ruff's own default
    set, which reported seven errors on a fresh adoption, every one of them in
    a file this template shipped (#108).
    """

    def test_the_config_seeds_to_the_python_packs(self):
        for pack in ("python", "python+typescript"):
            assert "ruff.toml" in {rel for rel, _ in adopt.seeds(ROOT, pack)}, pack

    def test_no_other_pack_receives_it(self):
        """A node project reads no ruff config, and a `none` project runs no lint gate."""
        for pack in ("typescript", "none"):
            assert "ruff.toml" not in {rel for rel, _ in adopt.seeds(ROOT, pack)}, pack

    def test_the_header_does_not_deny_it(self):
        """The header asserted the opposite until the manifest started claiming it."""
        assert "not seeded into a project" not in (ROOT / "ruff.toml").read_text()

    def test_the_python_packs_declare_the_command_that_reads_it(self):
        for pack in ("python", "python+typescript"):
            commands = {command for _, command, _ in adopt.PACKS[pack]}
            assert "uvx ruff check ." in commands, pack

    def test_the_note_explains_the_entry(self):
        declared = json.loads((ROOT / "seeds.json").read_text())
        assert "ruff.toml" in declared["note"]


class TestTheSeededNodeProject:
    """`package.json` and `tsconfig.json`, seeded to the packs whose gates run pnpm.

    `pnpm check` and `pnpm test` on a project with no manifest reported
    `ERR_PNPM_NO_IMPORTER_MANIFEST_FOUND` and failed two of three gates on the
    day the project was adopted (#112).
    """

    @staticmethod
    def declared(pack):
        return {rel for rel, _ in adopt.seeds(ROOT, pack)}

    def test_the_typescript_pack_takes_both_at_the_root(self):
        assert {"package.json", "tsconfig.json"} <= self.declared("typescript")

    def test_the_both_pack_takes_them_where_its_gates_run(self):
        seeded = self.declared("python+typescript")
        assert {"web/package.json", "web/tsconfig.json"} <= seeded
        assert not seeded & {"package.json", "tsconfig.json"}

    def test_a_pack_with_no_pnpm_gate_takes_neither(self):
        for pack in ("python", "none"):
            assert not self.declared(pack) & {"package.json", "tsconfig.json"}, pack

    def test_one_set_of_bytes_serves_both_packs(self):
        """The `web/` copies are a landing, so nothing here can drift from anything."""
        sources = dict(adopt.seeds(ROOT, "typescript")) | dict(
            adopt.seeds(ROOT, "python+typescript")
        )
        assert sources["package.json"] == sources["web/package.json"]
        assert sources["tsconfig.json"] == sources["web/tsconfig.json"]

    def test_it_declares_every_script_a_gate_invokes(self):
        """The seeded test asserts this from inside a project, and this from outside."""
        scripts = json.loads((ROOT / "package.json").read_text())["scripts"]
        for pack in ("typescript", "python+typescript"):
            for _, command, _ in adopt.PACKS[pack]:
                head, _, script = command.partition(" ")
                if head == "pnpm":
                    assert script in scripts, f"{pack} runs `{command}` and package.json cannot"

    def test_the_check_gate_has_something_to_check(self):
        """`tsc --noEmit` over an empty `include` exits on TS18003 and never on the code."""
        config = json.loads((ROOT / "tsconfig.json").read_text())
        assert config["compilerOptions"]["checkJs"] is True
        assert any(pattern.startswith("tests/") for pattern in config["include"])

    def test_the_note_explains_the_entries(self):
        declared = json.loads((ROOT / "seeds.json").read_text())
        assert "package.json" in declared["note"]
        assert "tsconfig.json" in declared["note"]


class TestALandedSeed:
    """A `per_pack` object names where a file lands, and a list keeps the template path."""

    @staticmethod
    def declare(template, per_pack, pack):
        (template / "seeds.json").write_text(json.dumps({"tracked": [], "per_pack": per_pack}))
        return dict(adopt.seeds(template, pack))

    def test_a_list_lands_a_file_where_the_template_holds_it(self, template):
        landed = self.declare(template, {"python": [STYLE], "none": []}, "python")
        assert set(landed) == {STYLE}
        assert landed[STYLE] == template / STYLE

    def test_an_object_lands_it_where_the_value_says(self, template):
        landed = self.declare(template, {"python": {STYLE: "web/STYLE.md"}, "none": []}, "python")
        assert set(landed) == {"web/STYLE.md"}
        assert landed["web/STYLE.md"] == template / STYLE

    def test_a_landed_file_is_written_to_its_landing(self, template, project):
        self.declare(template, {"python": {STYLE: "web/STYLE.md"}, "none": []}, "python")
        adopt.write(template, project, "python")
        assert (project / "web/STYLE.md").read_bytes() == (template / STYLE).read_bytes()
        assert not (project / STYLE).exists()

    def test_a_landed_file_is_recorded_under_its_landing(self, template, project):
        self.declare(template, {"python": {STYLE: "web/STYLE.md"}, "none": []}, "python")
        adopt.write(template, project, "python")
        assert "web/STYLE.md" in adopt.manifest(project)

    def test_a_rerun_over_a_landed_file_writes_nothing(self, template, project):
        self.declare(template, {"python": {STYLE: "web/STYLE.md"}, "none": []}, "python")
        adopt.write(template, project, "python")
        again = adopt.write(template, project, "python")
        assert [result.status for result in again] == [adopt.UNCHANGED]

    def test_an_object_withholds_its_template_path_from_the_expansion(self, template):
        """Withholding reads the keys, so a landed file is not seeded twice."""
        (template / "seeds.json").write_text(
            json.dumps(
                {
                    "tracked": ["docs/development/"],
                    "per_pack": {"python": {STYLE: "web/STYLE.md"}, "none": []},
                }
            )
        )
        assert STYLE not in {rel for rel, _ in adopt.seeds(template, "none")}


class TestTheGateRunAfterAFirstWrite:
    """A first write ends by running what it seeded, and reports without failing.

    The adoption is written whatever the gates say, so a red gate leaves
    `bin/adopt` at 0. An absent toolchain is reported without running anything,
    because `uvx ruff` on a machine with no uv fails under a gate name and says
    nothing about the machine.
    """

    @staticmethod
    def runner(project, exit_code):
        """A stand-in `bin/verify` in the project, exiting how the test wants."""
        (project / "bin").mkdir(exist_ok=True)
        path = project / "bin" / "verify"
        path.write_text(f"#!/bin/sh\necho the-runner-spoke\nexit {exit_code}\n")
        path.chmod(0o755)
        return path

    @staticmethod
    def everything_installed(monkeypatch):
        monkeypatch.setattr(adopt.shutil, "which", lambda name: f"/usr/bin/{name}")

    def test_a_project_without_the_runner_runs_nothing(self, project, capsys):
        assert adopt.run_gates(project, "python") == 0
        assert "nothing ran: bin/verify is not here" in capsys.readouterr().out

    def test_an_absent_toolchain_is_named_and_nothing_runs(self, project, capsys, monkeypatch):
        self.runner(project, 1)
        monkeypatch.setattr(adopt.shutil, "which", lambda name: None)
        assert adopt.run_gates(project, "python") == 0
        printed = capsys.readouterr().out
        assert "nothing ran: this machine has no uv" in printed
        assert "the-runner-spoke" not in printed

    def test_a_green_run_reports_and_returns_zero(self, project, capsys, monkeypatch):
        self.runner(project, 0)
        self.everything_installed(monkeypatch)
        assert adopt.run_gates(project, "python") == 0

    def test_a_red_gate_does_not_fail_the_adoption(self, project, capsys, monkeypatch):
        self.runner(project, 1)
        self.everything_installed(monkeypatch)
        assert adopt.run_gates(project, "python") == 1
        assert "The adoption is written" in capsys.readouterr().out

    def test_uv_is_wanted_whatever_the_pack_declares(self, monkeypatch):
        """`bin/verify` carries a `uv run --script` shebang, so uv runs every gate."""
        monkeypatch.setattr(adopt.shutil, "which", lambda name: None)
        assert "uv" in adopt.missing_tools("none")
        assert set(adopt.missing_tools("python")) == {"uv", "uvx"}

    def test_a_seeded_checker_needs_nothing_installed(self, monkeypatch):
        """`bin/check-style` arrives with the runner, so it is never looked up."""
        monkeypatch.setattr(adopt.shutil, "which", lambda name: None)
        assert "bin/check-style" not in adopt.missing_tools("python")

    def test_a_first_write_ends_with_the_gates(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "python", "--template", str(template)])
        assert "gates    " in capsys.readouterr().out

    def test_a_rerun_does_not_run_them_again(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "python", "--template", str(template)])
        capsys.readouterr()
        adopt.main([str(project), "--write", "--template", str(template)])
        assert "gates    " not in capsys.readouterr().out

    def test_a_plan_runs_nothing(self, template, project, capsys):
        adopt.main([str(project), "--pack", "python", "--template", str(template)])
        assert "gates    " not in capsys.readouterr().out

    def test_the_flag_skips_them(self, template, project, capsys):
        adopt.main(
            [str(project), "--write", "--pack", "python", "--no-gates", "--template", str(template)]
        )
        assert "gates    " not in capsys.readouterr().out


class TestTheInstallBeforeTheGateRun:
    """A pnpm pack installs before its gates run, and a python pack installs nothing.

    `pnpm check` runs `tsc`, which resolves from `node_modules/.bin`, so
    without an install the gate reports a missing binary and says nothing about
    the project's code (#112). The adoption is written whatever the install
    does, so a failure is printed and the gates run anyway.
    """

    @staticmethod
    def calls(monkeypatch):
        """Every `pnpm install` this run would make, without running one.

        The git calls `_record` and `default_phase` make go through the same
        function, so only the pnpm ones are collected.
        """
        seen = []

        def record(argv, **kwargs):
            if argv[0] == "pnpm":
                seen.append((argv, kwargs.get("cwd")))
            return subprocess.CompletedProcess(argv, 0, "", "")

        monkeypatch.setattr(adopt.subprocess, "run", record)
        return seen

    def test_a_python_pack_installs_nothing(self, project, monkeypatch):
        seen = self.calls(monkeypatch)
        adopt.install_pnpm(project, "python")
        assert seen == []

    def test_a_typescript_pack_installs_at_the_root(self, project, monkeypatch):
        seen = self.calls(monkeypatch)
        adopt.install_pnpm(project, "typescript")
        assert seen == [(["pnpm", "install"], project)]

    def test_the_both_pack_installs_where_its_gates_run(self, project, monkeypatch):
        (project / "web").mkdir()
        seen = self.calls(monkeypatch)
        adopt.install_pnpm(project, "python+typescript")
        assert seen == [(["pnpm", "install"], project / "web")]

    def test_an_absent_directory_installs_nothing_and_says_so(self, project, monkeypatch, capsys):
        seen = self.calls(monkeypatch)
        adopt.install_pnpm(project, "python+typescript")
        assert seen == []
        assert "no web/ to install into" in capsys.readouterr().out

    def test_a_failed_install_is_printed_and_the_gates_still_run(self, project, monkeypatch, capsys):
        monkeypatch.setattr(
            adopt.subprocess,
            "run",
            lambda argv, **kwargs: subprocess.CompletedProcess(argv, 1, "", "no network"),
        )
        adopt.install_pnpm(project, "typescript")
        printed = capsys.readouterr().out
        assert "no network" in printed
        assert "the gates run anyway" in printed

    def test_a_machine_with_no_pnpm_is_named_and_nothing_installs(self, project, capsys, monkeypatch):
        """`missing_tools` already reads the gate commands, and pnpm is one of them."""
        TestTheGateRunAfterAFirstWrite.runner(project, 0)
        monkeypatch.setattr(adopt.shutil, "which", lambda name: None)
        seen = self.calls(monkeypatch)
        assert adopt.run_gates(project, "typescript") == 0
        assert seen == []
        assert "nothing ran: this machine has no pnpm, uv" in capsys.readouterr().out

    def test_the_flag_skips_the_install_with_the_run(self, template, project, capsys, monkeypatch):
        seen = self.calls(monkeypatch)
        adopt.main(
            [
                str(project),
                "--write",
                "--pack",
                "typescript",
                "--no-gates",
                "--template",
                str(template),
            ]
        )
        assert seen == []
        assert "pnpm install" not in capsys.readouterr().out


class TestTheRecordedPack:
    """The manifest carries the pack, because a rerun that guessed it seeds the wrong driver."""

    def test_a_write_records_it(self, template, project):
        adopt.write(template, project, "python")
        assert adopt.recorded_pack(project) == "python"

    def test_a_project_with_no_manifest_records_nothing(self, project):
        assert adopt.recorded_pack(project) == ""

    def test_a_rerun_naming_no_pack_keeps_the_recorded_one(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "python", "--template", str(template)])
        capsys.readouterr()
        adopt.main([str(project), "--write", "--template", str(template)])
        assert adopt.recorded_pack(project) == "python"

    def test_a_project_adopted_before_the_record_is_asked_again(self, template, project, capsys):
        """The gate list and the workflow are already there, and the driver is not."""
        adopt.main([str(project), "--write", "--pack", "python", "--template", str(template)])
        manifest = project / adopt.MANIFEST_REL
        body = json.loads(manifest.read_text())
        del body["pack"]
        manifest.write_text(json.dumps(body))
        capsys.readouterr()
        assert adopt.main([str(project), "--write", "--template", str(template)]) == 2
        assert "--pack is required" in capsys.readouterr().err


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    """Run git in `root` with an identity of its own, never the machine's."""
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(root),
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True, env=env
    )


@pytest.fixture
def history(template):
    """The fixture template as a git repository, with every file committed."""
    git(template, "init", "-q")
    git(template, "add", "-A")
    git(template, "commit", "-qm", "first")
    return template


class TestTheRecordedCommit:
    """A sha that names bytes the project never received is the one field `--check` rests on.

    An adoption copies the working tree and records `HEAD`, so the two disagree
    for every run from a checkout with uncommitted changes, and
    `git show <sha>:<file>` then contradicts the file that landed.
    """

    def test_a_clean_checkout_records_its_head(self, history, project):
        adopt.write(history, project)
        assert adopt.recorded_commit(project) == git(history, "rev-parse", "HEAD").stdout.strip()

    def test_an_uncommitted_change_marks_the_sha(self, history, project):
        (history / STYLE).write_text("moved on\n")
        adopt.write(history, project)
        assert adopt.recorded_commit(project).endswith(adopt.DIRTY)

    def test_an_untracked_file_marks_it_too(self, history, project):
        """A directory entry expands over whatever is on disk, committed or not."""
        (history / ".claude" / "skills" / "demo" / "extra.md").write_text("new\n")
        adopt.write(history, project)
        assert adopt.recorded_commit(project).endswith(adopt.DIRTY)

    def test_the_marked_sha_still_names_the_commit(self, history, project):
        (history / STYLE).write_text("moved on\n")
        adopt.write(history, project)
        head = git(history, "rev-parse", "HEAD").stdout.strip()
        assert adopt.recorded_commit(project) == head + adopt.DIRTY

    def test_a_template_with_no_history_records_nothing(self, template, project):
        adopt.write(template, project)
        assert adopt.recorded_commit(project) == ""

    def test_a_project_with_no_manifest_records_nothing(self, project):
        assert adopt.recorded_commit(project) == ""


class TestTheDistance:
    def test_a_project_at_head_is_zero_commits_behind(self, history, project):
        adopt.write(history, project)
        assert adopt.commits_since(history, adopt.recorded_commit(project)) == 0

    def test_every_commit_since_is_counted(self, history, project):
        adopt.write(history, project)
        was = adopt.recorded_commit(project)
        for n in range(3):
            git(history, "commit", "-q", "--allow-empty", "-m", f"later {n}")
        assert adopt.commits_since(history, was) == 3

    def test_the_marker_does_not_stop_the_count(self, history, project):
        (history / STYLE).write_text("moved on\n")
        adopt.write(history, project)
        git(history, "commit", "-qam", "landed")
        assert adopt.commits_since(history, adopt.recorded_commit(project)) == 1

    def test_a_sha_this_history_does_not_carry_counts_nothing(self, history):
        assert adopt.commits_since(history, "0" * 40) is None

    def test_a_sha_that_is_no_ancestor_counts_nothing(self, history):
        """What a force push, a rebase or a second clone leaves in a manifest."""
        git(history, "checkout", "-q", "-b", "elsewhere")
        git(history, "commit", "-q", "--allow-empty", "-m", "a fork")
        forked = git(history, "rev-parse", "HEAD").stdout.strip()
        git(history, "checkout", "-q", "-")
        assert adopt.commits_since(history, forked) is None

    def test_a_template_with_no_history_counts_nothing(self, template):
        assert adopt.commits_since(template, "0" * 40) is None

    def test_no_recorded_sha_counts_nothing(self, history):
        assert adopt.commits_since(history, "") is None


class TestTheDriftCheck:
    """`--check` compares the template's bytes against the hashes the manifest recorded.

    Against the manifest and never against the recorded commit, so the file
    list holds when no count can be measured and on a machine with no git.
    """

    def test_a_project_adopted_from_this_template_is_level(self, template, project, capsys):
        adopt.write(template, project)
        assert adopt.check(template, project) == adopt.CHECK_LEVEL
        assert "No file this project copies has changed." in capsys.readouterr().out

    def test_a_moved_file_the_project_left_alone_is_taken(self, template, project, capsys):
        adopt.write(template, project)
        (template / STYLE).write_text("newer\n")
        assert adopt.check(template, project) == adopt.CHECK_BEHIND
        out = capsys.readouterr().out
        assert "1 tracked files changed:" in out
        assert "1 you have not edited   -> a rerun takes them" in out
        assert f"{adopt.UNEDITED:<9} {STYLE}" in out

    def test_a_moved_file_the_project_edited_is_sidecarred(self, template, project, capsys):
        adopt.write(template, project)
        (template / STYLE).write_text("newer\n")
        (project / STYLE).write_text("mine\n")
        assert adopt.check(template, project) == adopt.CHECK_BEHIND
        out = capsys.readouterr().out
        assert "1 you have edited       -> a rerun sidecars yours" in out
        assert f"{adopt.EDITED:<9} {STYLE}" in out

    def test_the_projects_own_edit_alone_is_no_drift(self, template, project, capsys):
        """A rerun still acts on it, and the template has not moved."""
        adopt.write(template, project)
        (project / STYLE).write_text("mine\n")
        assert adopt.check(template, project) == adopt.CHECK_LEVEL

    def test_a_file_the_project_deleted_counts_as_unedited(self, template, project, capsys):
        adopt.write(template, project)
        (template / STYLE).write_text("newer\n")
        (project / STYLE).unlink()
        assert adopt.check(template, project) == adopt.CHECK_BEHIND
        assert f"{adopt.UNEDITED:<9} {STYLE}" in capsys.readouterr().out

    def test_a_file_the_template_gained_is_unedited(self, template, project, capsys):
        adopt.write(template, project)
        (template / "docs" / "development" / "NEW.md").write_text("new\n")
        (template / "seeds.json").write_text(
            json.dumps({"tracked": [".claude/skills/", STYLE, "docs/development/NEW.md"]})
        )
        assert adopt.check(template, project) == adopt.CHECK_BEHIND
        assert f"{adopt.UNEDITED:<9} docs/development/NEW.md" in capsys.readouterr().out

    def test_a_path_the_template_stopped_shipping_is_named(self, template, project, capsys):
        adopt.write(template, project)
        (template / "seeds.json").write_text(json.dumps({"tracked": [".claude/skills/"]}))
        assert adopt.check(template, project) == adopt.CHECK_BEHIND
        out = capsys.readouterr().out
        assert f"{adopt.DROPPED:<9} {STYLE}" in out
        assert "gone from seeds.json" in out

    def test_a_project_with_no_manifest_is_unanswered(self, template, project, capsys):
        assert adopt.check(template, project) == adopt.CHECK_UNANSWERED
        assert "no adoption ever wrote here" in capsys.readouterr().out

    def test_the_commit_count_never_decides_the_exit_code(self, history, project, capsys):
        """A template that moved without touching a seeded file leaves the project current."""
        adopt.write(history, project)
        git(history, "commit", "-q", "--allow-empty", "-m", "somewhere else")
        assert adopt.check(history, project) == adopt.CHECK_LEVEL
        assert "moved 1 commits since this project adopted it" in capsys.readouterr().out

    def test_a_dirty_adoption_says_no_count_describes_it(self, history, project, capsys):
        (history / STYLE).write_text("uncommitted\n")
        adopt.write(history, project)
        adopt.check(history, project)
        assert "carrying uncommitted changes" in capsys.readouterr().out

    def test_a_sha_the_history_lost_says_so_and_still_lists_files(self, history, project, capsys):
        adopt.write(history, project)
        recorded = project / adopt.MANIFEST_REL
        body = json.loads(recorded.read_text())
        body["template"]["commit"] = "0" * 40
        recorded.write_text(json.dumps(body))
        (history / STYLE).write_text("newer\n")
        assert adopt.check(history, project) == adopt.CHECK_BEHIND
        out = capsys.readouterr().out
        assert "A force push, a rebase or a" in out
        assert f"{adopt.UNEDITED:<9} {STYLE}" in out

    def test_a_manifest_with_no_commit_says_so(self, template, project, capsys):
        adopt.write(template, project)
        assert adopt.check(template, project) == adopt.CHECK_LEVEL
        assert "records no template commit" in capsys.readouterr().out

    def test_a_level_project_names_no_file(self, history, project, capsys):
        adopt.write(history, project)
        adopt.check(history, project)
        assert "tracked files changed" not in capsys.readouterr().out


class TestTheCheckFlag:
    def test_it_writes_nothing(self, template, project, capsys):
        adopt.write(template, project)
        (template / STYLE).write_text("newer\n")
        adopt.main([str(project), "--check", "--template", str(template)])
        assert (project / STYLE).read_text() != "newer\n"

    def test_a_behind_project_exits_one(self, template, project, capsys):
        adopt.write(template, project)
        (template / STYLE).write_text("newer\n")
        assert adopt.main([str(project), "--check", "--template", str(template)]) == 1

    def test_a_level_project_exits_zero(self, template, project, capsys):
        adopt.write(template, project)
        assert adopt.main([str(project), "--check", "--template", str(template)]) == 0

    def test_it_needs_no_pack(self, template, project, capsys):
        """The recorded pack answers it, and a project asking this writes nothing."""
        adopt.main([str(project), "--write", "--pack", "python", "--template", str(template)])
        capsys.readouterr()
        assert adopt.main([str(project), "--check", "--template", str(template)]) == 0

    def test_it_does_not_run_with_write(self, template, project, capsys):
        adopt.write(template, project)
        assert adopt.main([str(project), "--check", "--write", "--template", str(template)]) == 2
        assert "does not run with --write" in capsys.readouterr().err

    def test_an_unadopted_directory_exits_two(self, template, project, capsys):
        assert adopt.main([str(project), "--check", "--template", str(template)]) == 2

    def test_the_rerun_it_names_is_the_one_that_takes_them(self, template, project, capsys):
        adopt.write(template, project)
        (template / STYLE).write_text("newer\n")
        adopt.main([str(project), "--check", "--template", str(template)])
        assert f"bin/adopt {project} --write" in capsys.readouterr().out


class TestAWithheldPathAlreadyInAProject:
    """The rerun for a project adopted before the exclusion landed.

    Nothing distinguishes a path dropped from `tracked` from one added to
    `template_only`: both leave a manifest row `seeds()` no longer names, which
    is the case `plan` reports as `removed`.
    """

    @pytest.fixture
    def withheld(self, template, project):
        """A project holding the demo skill after the template withheld it."""
        adopt.write(template, project)
        (template / "seeds.json").write_text(
            json.dumps({"tracked": [".claude/skills/", STYLE], "template_only": [".claude/skills/demo/"]})
        )
        return project / SKILL

    def test_a_plan_names_it_removed(self, template, project, withheld):
        assert statuses(adopt.plan(template, project))[SKILL] == adopt.REMOVED
        assert withheld.is_file()

    def test_a_write_deletes_it_and_the_directory_it_emptied(self, template, project, withheld):
        assert statuses(adopt.write(template, project))[SKILL] == adopt.REMOVED
        assert not (project / ".claude").exists()

    def test_its_row_goes_with_it(self, template, project, withheld):
        adopt.write(template, project)
        assert SKILL not in adopt.manifest(project)

    def test_an_edited_copy_stays_and_is_named(self, template, project, withheld):
        withheld.write_text("ours now\n")
        assert statuses(adopt.write(template, project))[SKILL] == adopt.ORPHANED
        assert withheld.read_text() == "ours now\n"

    def test_everything_still_seeded_is_untouched(self, template, project, withheld):
        assert statuses(adopt.write(template, project))[STYLE] == adopt.UNCHANGED


class TestFirstAdoption:
    def test_every_seeded_file_lands(self, template, project):
        results = adopt.write(template, project)
        assert statuses(results) == dict.fromkeys(ALL_SEEDED, adopt.WRITTEN)
        for rel in ALL_SEEDED:
            assert (project / rel).read_bytes() == (template / rel).read_bytes()

    def test_the_manifest_records_one_hash_per_file(self, template, project):
        adopt.write(template, project)
        recorded = adopt.manifest(project)
        assert set(recorded) == set(ALL_SEEDED)
        assert all(len(h) == 64 for h in recorded.values())

    def test_the_manifest_names_where_the_bytes_came_from(self, template, project):
        adopt.write(template, project)
        body = json.loads((project / adopt.MANIFEST_REL).read_text())
        assert body["template"]["origin"] == str(template)
        assert body["version"] == adopt.MANIFEST_VERSION


class TestRerun:
    def test_a_second_run_writes_nothing(self, template, project):
        adopt.write(template, project)
        before = (project / STYLE).stat().st_mtime_ns
        results = adopt.write(template, project)
        assert set(statuses(results).values()) == {adopt.UNCHANGED}
        assert (project / STYLE).stat().st_mtime_ns == before

    def test_a_second_run_leaves_no_sidecar(self, template, project):
        adopt.write(template, project)
        adopt.write(template, project)
        assert not list(project.rglob("*.local"))

    def test_a_lost_manifest_still_reports_unchanged(self, template, project):
        """The template and the target agree, so the manifest is never consulted."""
        adopt.write(template, project)
        (project / adopt.MANIFEST_REL).unlink()
        results = adopt.write(template, project)
        assert set(statuses(results).values()) == {adopt.UNCHANGED}

    def test_a_deleted_target_comes_back(self, template, project):
        adopt.write(template, project)
        (project / STYLE).unlink()
        assert statuses(adopt.write(template, project))[STYLE] == adopt.WRITTEN
        assert (project / STYLE).is_file()


class TestAnEditedFile:
    @pytest.fixture
    def edited(self, template, project):
        adopt.write(template, project)
        (project / STYLE).write_text("our own style guide\n")
        return project / STYLE

    def test_the_edit_is_kept_beside_the_new_version(self, edited, template, project):
        row = next(r for r in adopt.write(template, project) if r.rel == STYLE)
        assert row.status == adopt.KEPT
        assert row.sidecar == STYLE + ".local"
        assert (project / (STYLE + ".local")).read_text() == "our own style guide\n"

    def test_the_template_version_replaces_the_target(self, edited, template, project):
        adopt.write(template, project)
        assert edited.read_bytes() == (template / STYLE).read_bytes()

    def test_only_the_edited_file_grows_a_second_one(self, edited, template, project):
        adopt.write(template, project)
        assert [p.name for p in project.rglob("*.local")] == ["STYLE.md.local"]

    def test_a_file_this_template_never_wrote_counts_as_somebody_else_s(self, template, project):
        """No manifest row, so the bytes are theirs until proven otherwise."""
        (project / STYLE).parent.mkdir(parents=True)
        (project / STYLE).write_text("four hundred commits old\n")
        row = next(r for r in adopt.write(template, project) if r.rel == STYLE)
        assert row.status == adopt.KEPT
        assert (project / (STYLE + ".local")).read_text() == "four hundred commits old\n"


class TestAnUpstreamChange:
    def test_one_run_updates_the_untouched_file_and_keeps_the_edited_one(self, template, project):
        adopt.write(template, project)
        (project / STYLE).write_text("ours\n")
        (template / STYLE).write_text("a newer template style guide\n")
        (template / SKILL).write_text("a newer demo skill\n")

        results = statuses(adopt.write(template, project))
        assert results[SKILL] == adopt.UPDATED
        assert results[STYLE] == adopt.KEPT
        assert (project / SKILL).read_text() == "a newer demo skill\n"
        assert (project / STYLE).read_text() == "a newer template style guide\n"
        assert (project / (STYLE + ".local")).read_text() == "ours\n"

    def test_an_updated_file_leaves_no_sidecar(self, template, project):
        adopt.write(template, project)
        (template / SKILL).write_text("newer\n")
        adopt.write(template, project)
        assert not list(project.rglob("*.local"))


class TestAPathTheTemplateStoppedShipping:
    """The fifth outcome, keyed on a manifest row `seeds.json` no longer names.

    `plan` iterates the seed list, so a path seeded by an earlier run and since
    dropped was invisible to it. The file stayed in the project forever and its
    manifest row went on the next write, leaving nothing to say agentkit had
    ever put it there.
    """

    @pytest.fixture
    def dropped(self, template, project):
        """A project holding STYLE.md after the template stopped seeding it."""
        adopt.write(template, project)
        (template / "seeds.json").write_text(json.dumps({"tracked": [".claude/skills/"]}))
        return project / STYLE

    def test_a_plan_names_the_orphan_and_leaves_it_alone(self, template, project, dropped):
        assert statuses(adopt.plan(template, project))[STYLE] == adopt.REMOVED
        assert dropped.is_file()

    def test_a_write_deletes_it(self, template, project, dropped):
        assert statuses(adopt.write(template, project))[STYLE] == adopt.REMOVED
        assert not dropped.exists()

    def test_its_row_goes_with_it(self, template, project, dropped):
        adopt.write(template, project)
        assert STYLE not in adopt.manifest(project)

    def test_the_directory_it_emptied_goes_too(self, template, project, dropped):
        adopt.write(template, project)
        assert not (project / "docs").exists()

    def test_everything_still_seeded_is_untouched(self, template, project, dropped):
        assert statuses(adopt.write(template, project))[SKILL] == adopt.UNCHANGED

    def test_an_edited_orphan_stays(self, template, project, dropped):
        dropped.write_text("ours now\n")
        assert statuses(adopt.write(template, project))[STYLE] == adopt.ORPHANED
        assert dropped.read_text() == "ours now\n"

    def test_an_edited_orphan_grows_no_sidecar(self, template, project, dropped):
        """Nothing replaced it, so there is no second copy to move aside."""
        dropped.write_text("ours now\n")
        adopt.write(template, project)
        assert not list(project.rglob("*.local"))

    def test_an_edited_orphan_keeps_its_manifest_row(self, template, project, dropped):
        """The record of what agentkit wrote there, which is the half #41 lost."""
        was = adopt.manifest(project)[STYLE]
        dropped.write_text("ours now\n")
        adopt.write(template, project)
        assert adopt.manifest(project)[STYLE] == was

    def test_an_edited_orphan_is_named_on_every_later_run(self, template, project, dropped):
        dropped.write_text("ours now\n")
        adopt.write(template, project)
        assert statuses(adopt.write(template, project))[STYLE] == adopt.ORPHANED

    def test_an_orphan_deleted_by_hand_is_reported_nowhere(self, template, project, dropped):
        """No file, so no outcome. The row stays as the record of what was written."""
        dropped.unlink()
        assert STYLE not in statuses(adopt.write(template, project))
        assert STYLE in adopt.manifest(project)

    def test_a_row_this_template_still_seeds_is_never_an_orphan(self, template, project):
        adopt.write(template, project)
        rows = statuses(adopt.write(template, project))
        assert adopt.REMOVED not in rows.values()
        assert adopt.ORPHANED not in rows.values()


class TestARenamedSkill:
    """`seeds.json` tracks `.claude/skills/` as a directory, so a rename upstream
    leaves the old `SKILL.md` in the target. A skill directory that exists loads,
    and the orphan competes for the same triggers as its replacement.
    """

    @pytest.fixture
    def renamed(self, template, project):
        adopt.write(template, project)
        skills = template / ".claude" / "skills"
        (skills / "demo").rename(skills / "planner")
        return project

    def test_the_old_skill_goes_and_the_new_one_lands(self, template, renamed):
        rows = statuses(adopt.write(template, renamed))
        assert rows[SKILL] == adopt.REMOVED
        assert rows[".claude/skills/planner/SKILL.md"] == adopt.WRITTEN
        assert not (renamed / ".claude" / "skills" / "demo").exists()

    def test_an_edited_old_skill_stays_beside_its_replacement(self, template, renamed):
        (renamed / SKILL).write_text("our own trigger list\n")
        rows = statuses(adopt.write(template, renamed))
        assert rows[SKILL] == adopt.ORPHANED
        assert (renamed / SKILL).read_text() == "our own trigger list\n"
        assert (renamed / ".claude" / "skills" / "planner" / "SKILL.md").is_file()

    def test_the_directory_holding_an_edited_skill_survives(self, template, renamed):
        """Its unedited sibling is removed, and the directory stays because the skill does."""
        (renamed / SKILL).write_text("our own trigger list\n")
        adopt.write(template, renamed)
        assert not (renamed / ".claude" / "skills" / "demo" / "reference.md").exists()
        assert (renamed / ".claude" / "skills" / "demo").is_dir()


class TestWhyNothingRecordsTheProjectsOwnBytes:
    """The argument against an `--adopt-existing` mode, as a test.

    A baseline mode would record the project's current bytes in the manifest.
    The manifest then means "these bytes were here once" rather than "these
    bytes came from the template", and the next run reads that row as
    permission to replace the file with no sidecar. The overwrite below is
    what such a mode would cost on the second run.
    """

    def test_a_manifest_row_matching_the_projects_own_bytes_yields_a_silent_overwrite(self, template, project):
        theirs = "four hundred commits of their own rules\n"
        (project / STYLE).parent.mkdir(parents=True)
        (project / STYLE).write_text(theirs)
        adopt._record(
            template,
            project,
            {STYLE: hashlib.sha256(theirs.encode()).hexdigest()},
        )

        row = next(r for r in adopt.write(template, project) if r.rel == STYLE)
        assert row.status == adopt.UPDATED
        assert row.sidecar is None
        assert not (project / (STYLE + ".local")).exists()
        assert (project / STYLE).read_bytes() == (template / STYLE).read_bytes()


class TestAPlanChangesNothing:
    def test_a_plan_writes_no_file(self, template, project):
        rows = adopt.plan(template, project)
        assert set(statuses(rows).values()) == {adopt.WRITTEN}
        assert list(project.iterdir()) == []

    def test_a_plan_records_no_manifest(self, template, project):
        adopt.plan(template, project)
        assert not (project / adopt.MANIFEST_REL).exists()


class TestTheTeamLayer:
    @pytest.fixture
    def answers(self):
        return ANSWERS

    def test_all_three_files_are_seeded(self, project, answers):
        rows = adopt.seed_team(project, answers)
        assert statuses(rows) == {
            ".agentkit/gates.toml": "seeded",
            ".agentkit/phase.json": "seeded",
            ".agentkit/team.md": "seeded",
        }

    def test_a_second_run_leaves_an_edited_gate_list_alone(self, project, answers):
        adopt.seed_team(project, answers)
        (project / ".agentkit" / "gates.toml").write_text("# ours\n")
        rows = adopt.seed_team(project, answers)
        assert statuses(rows)[".agentkit/gates.toml"] == "present"
        assert (project / ".agentkit" / "gates.toml").read_text() == "# ours\n"

    @pytest.mark.parametrize("pack", sorted(adopt.PACKS))
    def test_every_pack_writes_a_gate_list_a_parser_reads(self, project, answers, pack):
        adopt.seed_team(project, {**answers, "pack": pack})
        parsed = tomllib.loads((project / ".agentkit" / "gates.toml").read_text())
        gates = parsed.get("gate", [])
        assert [g["name"] for g in gates] == [name for name, _, _ in adopt.PACKS[pack]]
        # `command` is what bin/verify reads. `run` was the key here until #3 and
        # the runner exits on it before running anything.
        assert [g["command"] for g in gates] == [c for _, c, _ in adopt.PACKS[pack]]
        assert [g.get("cwd") for g in gates] == [cwd for _, _, cwd in adopt.PACKS[pack]]

    def test_no_seeded_command_needs_a_shell(self, project, answers):
        """The runner uses shlex and no shell, so `cd x && y` looks for a binary named cd."""
        for pack in adopt.PACKS:
            for name, command, _ in adopt.PACKS[pack]:
                assert "&&" not in command and not command.startswith("cd "), f"{pack}/{name}"

    def test_the_phase_is_machine_readable(self, project, answers):
        adopt.seed_team(project, answers)
        assert json.loads((project / ".agentkit" / "phase.json").read_text())["phase"] == "building"

    def test_the_answers_reach_the_team_file(self, project, answers):
        adopt.seed_team(project, answers)
        body = (project / ".agentkit" / "team.md").read_text()
        assert "# demo" in body
        assert "A project." in body
        assert "Both of us review." in body

    def test_the_owner_section_says_nobody_has_been_asked(self, project, answers):
        """An empty table row reads as a bug, and an agent filled it in (#145)."""
        adopt.seed_team(project, answers)
        body = (project / ".agentkit" / "team.md").read_text()
        assert "## Who owns what" in body
        assert "Nobody has been asked" in body
        assert "|  |" not in body

    def test_the_team_layer_is_never_in_the_manifest(self, template, project, answers):
        adopt.write(template, project)
        adopt.seed_team(project, answers)
        assert not any(rel.startswith(".agentkit/") for rel in adopt.manifest(project))


class TestTheCommand:
    def test_writing_needs_a_pack_the_first_time(self, template, project, capsys):
        assert adopt.main([str(project), "--write", "--template", str(template)]) == 2
        assert "--pack is required" in capsys.readouterr().err
        assert list(project.iterdir()) == []

    def test_a_plan_needs_no_pack(self, template, project, capsys):
        assert adopt.main([str(project), "--template", str(template)]) == 0
        out = capsys.readouterr().out
        assert "plan only, nothing written" in out
        assert list(project.iterdir()) == []

    def test_a_plan_names_every_file(self, template, project, capsys):
        adopt.main([str(project), "--template", str(template)])
        out = capsys.readouterr().out
        for rel in ALL_SEEDED:
            assert rel in out

    def test_the_output_names_both_files_when_an_edit_is_kept(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        (project / STYLE).write_text("ours\n")
        capsys.readouterr()
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        out = capsys.readouterr().out
        kept = next(line for line in out.splitlines() if adopt.KEPT in line)
        assert STYLE in kept
        assert STYLE + ".local" in kept

    def test_the_plan_names_an_orphan_and_says_it_would_go(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        (template / "seeds.json").write_text(json.dumps({"tracked": [".claude/skills/"]}))
        capsys.readouterr()
        adopt.main([str(project), "--template", str(template)])
        out = capsys.readouterr().out
        assert f"{adopt.REMOVED:<9} {STYLE}" in out
        assert "still hash to what the manifest recorded" in out
        assert (project / STYLE).is_file()

    def test_an_edited_orphan_gets_a_paragraph_of_its_own(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        (template / "seeds.json").write_text(json.dumps({"tracked": [".claude/skills/"]}))
        (project / STYLE).write_text("ours now\n")
        capsys.readouterr()
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        out = capsys.readouterr().out
        assert f"{adopt.ORPHANED:<9} {STYLE}" in out
        assert "competes for its" in out

    def test_a_kept_file_gets_a_paragraph_of_its_own(self, template, project, capsys):
        (project / STYLE).parent.mkdir(parents=True)
        (project / STYLE).write_text("theirs\n")
        adopt.main([str(project), "--template", str(template)])
        assert "already exist here and differ from the template" in capsys.readouterr().out

    def test_a_missing_project_directory_stops(self, template, tmp_path, capsys):
        assert adopt.main([str(tmp_path / "nowhere"), "--template", str(template)]) == 2
        assert "not a directory" in capsys.readouterr().err

    def test_the_name_defaults_to_the_directory(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert "# project" in (project / ".agentkit" / "team.md").read_text()


class TestThePackTheOutputNames:
    """One header line on the plan and on the write, naming the pack rendered.

    `per_pack` gives each pack a file set no other pack has, so a plan that
    names no pack is approved as though it were every pack's and a write under
    another one lands a different set (#164).
    """

    def flags(self, template):
        return ["--template", str(template), "--no-gates", "--no-labels"]

    def test_a_plan_that_was_given_no_pack_names_the_one_it_assumed(self, template, project, capsys):
        adopt.main([str(project), *self.flags(template)])
        assert "pack     none, the default." in capsys.readouterr().out

    def test_a_plan_names_the_pack_it_was_given(self, template, project, capsys):
        adopt.main([str(project), "--pack", "typescript", *self.flags(template)])
        assert "pack     typescript, given with --pack." in capsys.readouterr().out

    def test_a_write_names_its_pack(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "typescript", *self.flags(template)])
        assert "pack     typescript, given with --pack." in capsys.readouterr().out

    def test_a_rerun_that_names_no_pack_reports_the_recorded_one(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "python", *self.flags(template)])
        capsys.readouterr()
        adopt.main([str(project), *self.flags(template)])
        assert "pack     python, recorded by the last adoption." in capsys.readouterr().out


class TestThePhaseDefault:
    def test_a_directory_with_no_history_is_shaping(self, project):
        assert adopt.default_phase(project) == "shaping"

    def test_a_repository_with_a_commit_is_building(self, project):
        import subprocess

        for args in (["init"], ["commit", "--allow-empty", "-m", "first"]):
            subprocess.run(
                ["git", "-C", str(project), *args],
                check=True,
                capture_output=True,
                env={"PATH": "/usr/bin:/bin", "HOME": str(project), "GIT_AUTHOR_NAME": "t",
                     "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
            )
        assert adopt.default_phase(project) == "building"


class TestTheDesignSettings:
    """`## Design` in `team.md`, which `bin/adopt` and this repository both write.

    #26: this repository's `.agentkit/team.md` was written by hand to match
    `team_files()`, and nothing checked the two agree.
    """

    def test_the_design_settings_are_surface_and_review(self, project):
        """#123 removed `references`, and a stale row would read as answerable."""
        adopt.seed_team(project, ANSWERS)
        body = (project / ".agentkit" / "team.md").read_text()
        assert "| surface | canvas, file, none |" in body
        assert "| review | artifact, paper, none |" in body
        assert "references" not in body.split("## Design", 1)[1]

    def test_review_seeds_as_its_default_with_no_question(self, project):
        """#193: the medium has a default, so it renders answered every time.

        `surface` is the opposite case, and rendering the two the same way
        would tell a reader that the artifact medium is a choice nobody made.
        """
        adopt.seed_team(project, ANSWERS)
        body = (project / ".agentkit" / "team.md").read_text().split("## Design", 1)[1]
        assert "**`review` is `artifact`.**" in body

    def test_no_review_flag_exists(self, template, project):
        """#193 seeds the row and adds no seventh answer, so argparse refuses one."""
        with pytest.raises(SystemExit):
            adopt.main([str(project), "--write", "--pack", "none", "--review", "paper",
                        "--template", str(template)])

    def test_surface_is_seeded_unanswered(self, project):
        adopt.seed_team(project, ANSWERS)
        body = (project / ".agentkit" / "team.md").read_text()
        assert "| surface | canvas, file, none |" in body
        assert "`surface` waits until somebody picks one." in body

    def test_an_answered_surface_is_written_where_the_question_was(self, project):
        """#162: the skill asks for it in its first call and nothing recorded it."""
        adopt.seed_team(project, {**ANSWERS, "surface": "file, design/"})
        body = (project / ".agentkit" / "team.md").read_text()
        assert "**demo: surface `file, design/`.**" in body
        assert "waits until somebody picks one" not in body

    def test_the_flag_carries_the_answer_into_the_team_file(self, template, project):
        adopt.main(
            [str(project), "--write", "--pack", "none", "--surface", "file, design/",
             "--template", str(template), "--no-gates", "--no-labels"]
        )
        body = (project / ".agentkit" / "team.md").read_text()
        assert "surface `file, design/`" in body
        assert "waits until somebody picks one" not in body

    def test_a_write_with_no_flag_leaves_the_question_open(self, template, project):
        adopt.main(
            [str(project), "--write", "--pack", "none",
             "--template", str(template), "--no-gates", "--no-labels"]
        )
        assert "`surface` waits until somebody picks one." in (project / ".agentkit" / "team.md").read_text()

    def test_the_command_names_no_references_flag(self, template, project):
        """#123: the flag came out with the setting, and argparse would accept
        a stale `--references` silently if it had stayed as a no-op."""
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert "references" not in (project / ".agentkit" / "team.md").read_text().split("## Design", 1)[1]
        with pytest.raises(SystemExit):
            adopt.main([str(project), "--write", "--pack", "none", "--references", "refero", "--template", str(template)])


def headings(body: str) -> list[str]:
    """Every `## ` heading, in the order the file states them."""
    return re.findall(r"^## (.+)$", body, re.M)


def section(body: str, heading: str) -> str:
    """One `## ` section's text, up to the next heading or the end of the file."""
    return body.split(f"## {heading}\n")[1].split("\n## ")[0]


def words(text: str) -> str:
    """The text with every run of whitespace collapsed, so line wrapping stops mattering."""
    return " ".join(text.split())


class TestThisRepositorysOwnTeamLayer:
    """`.agentkit/team.md` and `.agentkit/phase.json` here, against what `team_files()` renders.

    Both were written by hand in PR #22 to match the renderer, and nothing
    checked they still agree (#26). `bin/adopt --write` does not run against
    this repository, so a test carries the check instead. What the two copies
    share is the format: the headings, the design table, and the paragraph
    saying which layer the file is. Every other section here holds an answer
    the seeded copy leaves open, and those diverge on purpose.
    """

    def ours(self) -> str:
        return (ROOT / ".agentkit" / "team.md").read_text()

    def rendered(self) -> str:
        return adopt.team_files(ANSWERS)["team.md"]

    def test_the_phase_file_is_byte_for_byte_what_adopt_renders(self):
        """The whole file, because it carries a format and no prose."""
        ours = (ROOT / ".agentkit" / "phase.json").read_text()
        answers = {**ANSWERS, "phase": json.loads(ours)["phase"]}
        assert ours == adopt.team_files(answers)["phase.json"]

    def test_the_headings_are_the_same_list_in_the_same_order(self):
        """A section on one side and not the other is the divergence #26 named.

        Added here and missing from the renderer, every adopted project gets a
        team layer without it. Added to the renderer and missing here, this
        repository is running a team layer a project would not recognise.
        """
        assert headings(self.ours()) == headings(self.rendered())

    def test_the_design_table_is_the_one_adopt_writes(self):
        """The one block both files carry verbatim, and the one the design skills read."""
        assert adopt.DESIGN_TABLE in self.ours()

    def test_the_layer_paragraph_says_what_adopt_writes(self):
        """Ours wraps wider than the renderer, so the comparison is on the words."""
        heading = "The layer this file is"
        assert words(section(self.ours(), heading)) == words(section(self.rendered(), heading))


def rule_numbers(body: str) -> set[int]:
    """Every rule this router states, from its `## N.` and `## N to M` headings."""
    found: set[int] = set()
    for one, last in re.findall(r"^## (\d+)(?:\.|\s+to\s+(\d+))", body, re.M):
        found |= set(range(int(one), int(last) + 1)) if last else {int(one)}
    return found


class TestTheRouter:
    def test_it_lands_in_an_empty_project(self, template, project):
        row = adopt.seed_router(template, project, ANSWERS)
        assert row.status == adopt.SEEDED
        assert (project / "CLAUDE.md").is_file()

    def test_the_answers_reach_it(self, template, project):
        adopt.seed_router(template, project, ANSWERS)
        body = (project / "CLAUDE.md").read_text()
        assert body.startswith("# demo\n")
        assert "A project." in body

    def test_no_placeholder_survives(self, template, project):
        """The reason the router is rendered rather than copied from a template file.

        A skipped question raises `KeyError` in `str.format`, so no `{name}`
        reaches a project's tree. A missing key would fail this test at the
        render, before the assertion.
        """
        adopt.seed_router(template, project, ANSWERS)
        body = (project / "CLAUDE.md").read_text()
        assert "{" not in body and "}" not in body

    def test_an_existing_router_is_left_exactly_as_it_was(self, template, project):
        theirs = "# their own project\n\nRules nobody here wrote.\n"
        (project / "CLAUDE.md").write_text(theirs)
        row = adopt.seed_router(template, project, ANSWERS)
        assert row.status == adopt.PRESENT
        assert (project / "CLAUDE.md").read_text() == theirs
        assert not (project / "CLAUDE.md.local").exists()

    def test_a_plan_writes_no_router(self, project):
        assert adopt.plan_router(project).status == adopt.SEEDED
        assert not (project / "CLAUDE.md").exists()

    def test_it_is_never_in_the_manifest(self, template, project):
        adopt.write(template, project)
        adopt.seed_router(template, project, ANSWERS)
        assert "CLAUDE.md" not in adopt.manifest(project)

    def test_a_rerun_leaves_the_projects_own_rules_alone(self, template, project):
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        mine = (project / "CLAUDE.md").read_text() + "\n## 1. Everything is a file.\n"
        (project / "CLAUDE.md").write_text(mine)
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert (project / "CLAUDE.md").read_text() == mine

    def test_the_rules_it_states_are_the_ones_this_repository_states(self, template):
        """The agreement test STYLE.md asks for when a fact lives in two files.

        A project gets rules 0, 9, 20 and 24 from the generated router and
        nowhere else, so the text is a second copy of the set in this
        repository's `CLAUDE.md`. Coupling this one test to the real tree is
        what makes a rule added there without being added here fail.
        """
        seeded = rule_numbers(adopt.router(template, ANSWERS))
        shipped = rule_numbers((ROOT / "CLAUDE.md").read_text())
        assert seeded == shipped
        assert {0, 1, 8, 9, 20, 24} <= seeded

    def test_the_opening_agrees_with_this_repositorys_own(self, template):
        """Which rules a check catches and which a reader carries, stated in two files.

        A project gets that split from the generated router and nowhere else,
        so a correction made here and skipped in `CLAUDE.md` leaves the two
        describing different mechanisms (#42).
        """

        def opening(body: str) -> str:
            return body.split("# Rules:", 1)[1].split("\n## ", 1)[0]

        assert opening(adopt.router(template, ANSWERS)) == opening((ROOT / "CLAUDE.md").read_text())

    def test_rules_1_to_8_carry_no_constraint_and_nothing_to_fill_in(self, template):
        """An empty heading invites a guess and a question list invites an answer."""
        section = self.held_open(adopt.router(template, ANSWERS))
        assert "?" not in section
        assert "- " not in section
        assert "TODO" not in section

    def test_the_numbers_held_open_name_the_skill_that_fills_them(self, template):
        """A held-open section pointing at nothing gets filled by whoever reads it.

        The note is the whole defence: an agent that finds eight numbers, no
        content and no instruction writes what the codebase implies, and a
        guess there reads as settled to every session after it.
        """
        assert "`shape`" in self.held_open(adopt.router(template, ANSWERS))

    def test_the_skill_it_names_is_one_the_project_gets(self):
        """A router naming a skill `seeds.json` skips is a broken instruction."""
        seeded = {rel for rel, _ in adopt.seeds(ROOT)}
        assert ".claude/skills/shape/SKILL.md" in seeded

    def test_a_rerun_leaves_a_shaped_section_alone(self, template, project):
        """`shape` and `adopt` write into one file and never over each other (#23).

        `shape` replaces what sits between the held-open heading and rule 9.
        The router carries no manifest row and `seed_router` returns on any
        file that exists, so an update of the scaffolding reports `present` and
        writes nothing. The rule survives because nothing here is claimed by
        the manifest, which is the only reason it survives.
        """
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        shaped = re.sub(
            r"## 1 to 8 are yours.*?(?=\n## 9\.)",
            "## 1. Every hour on a screen was measured\n\n"
            "A number this project inferred says so where it is shown.\n",
            (project / "CLAUDE.md").read_text(),
            flags=re.S,
        )
        assert "## 1. Every hour" in shaped
        (project / "CLAUDE.md").write_text(shaped)
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert (project / "CLAUDE.md").read_text() == shaped

    @staticmethod
    def held_open(body: str) -> str:
        """The numbers a project fills, from the heading to the next rule."""
        return body.split("## 1 to 8")[1].split("\n## ")[0]


class TestTheRoleTable:
    def test_every_seeded_guide_gets_a_row(self):
        table = adopt.role_table(ROOT)
        for name in ("ENGINEER.md", "DESIGNER.md", "OPERATOR.md"):
            assert f"docs/roles/{name}" in table

    def test_every_guide_this_repository_ships_has_a_description(self):
        """A row reading `unstated` means somebody added a guide and no summary."""
        assert "unstated" not in adopt.role_table(ROOT)

    def test_a_template_with_no_guides_says_so_instead_of_printing_an_empty_table(self, template):
        assert "seeds no role guides" in adopt.role_table(template)

    def test_the_router_names_the_guides_a_project_actually_gets(self):
        body = adopt.router(ROOT, ANSWERS)
        for path in sorted((ROOT / "docs" / "roles").glob("*.md")):
            assert path.name in body

    def test_the_guides_are_seeded(self):
        """A guide the router names and `seeds.json` skips is a broken link."""
        seeded = {rel for rel, _ in adopt.seeds(ROOT)}
        for path in sorted((ROOT / "docs" / "roles").glob("*.md")):
            assert f"docs/roles/{path.name}" in seeded


class TestTheCommandOnAnExistingRouter:
    def test_the_report_names_the_router_either_way(self, template, project, capsys):
        adopt.main([str(project), "--template", str(template)])
        out = capsys.readouterr().out
        assert "router" in out
        assert f"{adopt.SEEDED:<9} CLAUDE.md" in out

    def test_a_present_router_gets_a_paragraph_of_its_own(self, template, project, capsys):
        (project / "CLAUDE.md").write_text("# theirs\n")
        adopt.main([str(project), "--template", str(template)])
        out = capsys.readouterr().out
        assert "Nothing was written, nothing was moved" in out
        assert "the `adopt` skill asks" in out

    def test_a_write_against_an_existing_router_still_seeds_the_rest(self, template, project):
        (project / "CLAUDE.md").write_text("# theirs\n")
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert (project / "CLAUDE.md").read_text() == "# theirs\n"
        assert (project / ".agentkit" / "team.md").is_file()
        assert (project / STYLE).is_file()


class TestTheWorkflows:
    """`.github/workflows/`, the only thing that runs any of this unprompted.

    The seeded gates workflow names no gate. Every step of this repository's
    own file used to be `bin/verify <name>`, and a copy of it in a project
    seeded from the python pack failed on step two with `No gate named probes`,
    measured 2026-08-29.
    """

    @pytest.mark.parametrize("pack", sorted(adopt.PACKS))
    def test_the_gates_workflow_names_no_gate(self, pack):
        body = adopt.gates_workflow(pack)
        for name, _, _ in adopt.PACKS[pack]:
            assert f"bin/verify {name}" not in body
        assert "      - run: bin/verify\n" in body

    @pytest.mark.parametrize("pack", sorted(adopt.PACKS))
    def test_every_pack_installs_uv(self, pack):
        """`bin/verify` runs under `uv run --script` whatever the gates name."""
        assert "astral-sh/setup-uv" in adopt.gates_workflow(pack)

    @pytest.mark.parametrize("pack", sorted(adopt.PACKS))
    def test_a_pnpm_gate_gets_node_and_an_install_where_it_runs(self, pack):
        body = adopt.gates_workflow(pack)
        where = adopt.pnpm_dirs(pack)
        assert ("pnpm/action-setup" in body) == bool(where)
        assert body.count("pnpm install") == len(where)
        for directory in where:
            if directory != ".":
                assert f"working-directory: {directory}" in body

    def test_the_pnpm_install_follows_the_gates_working_directory(self):
        """The `python+typescript` pack runs its two pnpm gates in `web/`."""
        assert adopt.pnpm_dirs("python+typescript") == ["web"]
        assert "        working-directory: web\n" in adopt.gates_workflow("python+typescript")

    def test_both_land_in_an_empty_project(self, project):
        rows = adopt.seed_workflows(project, ANSWERS)
        assert statuses(rows) == {
            ".github/workflows/gates.yml": adopt.SEEDED,
            ".github/workflows/process.yml": adopt.SEEDED,
        }

    def test_a_rerun_leaves_an_edited_workflow_alone(self, project):
        """A replaced workflow leaves the project's edit in a `.local` GitHub never runs."""
        adopt.seed_workflows(project, ANSWERS)
        edited = project / ".github" / "workflows" / "gates.yml"
        edited.write_text("# ours\n")
        rows = adopt.seed_workflows(project, ANSWERS)
        assert statuses(rows)[".github/workflows/gates.yml"] == adopt.PRESENT
        assert edited.read_text() == "# ours\n"
        assert not list(project.rglob("*.local"))

    def test_they_are_never_in_the_manifest(self, template, project):
        adopt.write(template, project)
        adopt.seed_workflows(project, ANSWERS)
        assert not any(rel.startswith(".github/") for rel in adopt.manifest(project))

    def test_a_plan_writes_neither(self, project):
        assert {row.status for row in adopt.plan_workflows(project)} == {adopt.SEEDED}
        assert not (project / ".github").exists()

    def test_the_plan_names_what_a_write_seeds(self, project):
        planned = {row.rel for row in adopt.plan_workflows(project)}
        assert planned == {f"{adopt.WORKFLOWS_DIR}/{name}" for name in adopt.workflow_files(ANSWERS)}

    def test_the_process_workflow_says_what_an_unconfigured_project_gets(self):
        """`.agentkit/process.toml` is never seeded, so the file has to say so."""
        body = adopt.workflow_files(ANSWERS)["process.yml"]
        assert ".agentkit/process.toml" in body
        assert "absent" in body
        assert "bin/check-process" in body

    def test_a_write_seeds_both_and_the_report_names_them(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "python", "--template", str(template)])
        out = capsys.readouterr().out
        for name in adopt.WORKFLOW_FILES:
            assert (project / ".github" / "workflows" / name).is_file()
            assert f"{adopt.WORKFLOWS_DIR}/{name}" in out

    def test_a_rerun_missing_only_the_workflow_asks_for_the_pack_again(self, template, project, capsys):
        """A workflow rendered from a defaulted `none` installs no pnpm."""
        adopt.main([str(project), "--write", "--pack", "typescript", "--template", str(template)])
        import shutil

        shutil.rmtree(project / ".github")
        capsys.readouterr()
        assert adopt.main([str(project), "--write", "--template", str(template)]) == 2
        assert "--pack is required" in capsys.readouterr().err
        assert not (project / ".github").exists()


class TestWhatThePlanKnowsWithoutTheAnswers:
    """A plan renders nothing, so it holds a name list the renderer has to match."""

    def test_the_team_file_names_agree(self):
        assert set(adopt.TEAM_FILES) == set(adopt.team_files(ANSWERS))

    def test_the_workflow_names_agree(self):
        assert set(adopt.WORKFLOW_FILES) == set(adopt.workflow_files(ANSWERS))


class TestTheRunnerAnswer:
    """`--runner`, the seventh answer, and what `local` renders (#194).

    `cloud` renders what every adoption rendered before the answer existed,
    so its tests pin the absence: no self-hosted line, no preflight job, no
    runner section in the team layer. A hosted project reads nothing about
    runners.
    """

    LOCAL = {**ANSWERS, "runner": "local"}

    def test_the_label_comes_from_the_slug(self):
        assert adopt.runner_label("Demo App") == "demo-app-local"

    def test_local_puts_the_gates_job_on_the_runner(self):
        body = adopt.workflow_files(self.LOCAL)["gates.yml"]
        assert "    runs-on: [self-hosted, demo-local]\n" in body

    def test_local_adds_the_preflight_job_on_hosted_minutes(self):
        """The job that watches the runner cannot run on the runner it watches."""
        body = adopt.workflow_files(self.LOCAL)["gates.yml"]
        assert "  preflight:\n" in body
        assert body.count("    runs-on: ubuntu-latest\n") == 1
        assert "No runner labelled demo-local" in body

    def test_the_preflight_fires_once_per_pull_request(self):
        """`synchronize` would bill a hosted minute per push, which is what `local` avoids."""
        body = adopt.workflow_files(self.LOCAL)["gates.yml"]
        assert "github.event.action == 'opened'" in body
        assert "'synchronize'" not in body.split("preflight:")[1]

    def test_local_puts_both_process_jobs_on_the_runner(self):
        body = adopt.workflow_files(self.LOCAL)["process.yml"]
        assert body.count("    runs-on: [self-hosted, demo-local]\n") == 2
        assert "ubuntu-latest" not in body

    def test_local_renders_the_team_layer_section(self):
        body = adopt.team_files(self.LOCAL)["team.md"]
        assert "self-hosted runner, label `demo-local`" in body

    def test_cloud_renders_none_of_it(self):
        flows = adopt.workflow_files(ANSWERS)
        assert "self-hosted" not in flows["gates.yml"] + flows["process.yml"]
        assert "preflight" not in flows["gates.yml"]
        assert "runner" not in adopt.team_files(ANSWERS)["team.md"]

    def _visibility(self, answer):
        import subprocess

        def fake(project, *args):
            assert "repo" in args
            return subprocess.CompletedProcess(args, 0, stdout=answer + "\n", stderr="")

        return fake

    def test_local_is_refused_on_a_public_repository(self, template, project, monkeypatch, capsys):
        monkeypatch.setattr(adopt, "_gh", self._visibility("PUBLIC"))
        code = adopt.main(
            [str(project), "--write", "--pack", "python", "--runner", "local", "--template", str(template)]
        )
        assert code == 2
        assert "fork" in capsys.readouterr().err
        assert not (project / ".agentkit").exists()

    def test_local_writes_on_a_private_repository(self, template, project, monkeypatch):
        monkeypatch.setattr(adopt, "_gh", self._visibility("PRIVATE"))
        adopt.main(
            [
                str(project),
                "--write",
                "--pack",
                "python",
                "--runner",
                "local",
                "--template",
                str(template),
                "--no-gates",
                "--no-labels",
            ]
        )
        body = (project / ".github" / "workflows" / "gates.yml").read_text()
        assert "    runs-on: [self-hosted, project-local]\n" in body

    def test_unreadable_visibility_warns_and_writes(self, template, project, monkeypatch, capsys):
        monkeypatch.setattr(adopt, "_gh", lambda *a: None)
        adopt.main(
            [
                str(project),
                "--write",
                "--pack",
                "python",
                "--runner",
                "local",
                "--template",
                str(template),
                "--no-gates",
                "--no-labels",
            ]
        )
        assert "visibility" in capsys.readouterr().out
        assert (project / ".github" / "workflows" / "gates.yml").is_file()


class TestTheIgnoreFile:
    """`.gitignore`, the one target where this template merges into a project's file.

    Rule 0 calls `.agentkit/local.md` gitignored and nothing wrote a
    `.gitignore`, so a seeded project was one `git add` from committing the
    personal layer (#48).
    """

    def read(self, project):
        return (project / ".gitignore").read_text()

    def test_an_empty_project_gets_the_block(self, project):
        assert adopt.seed_gitignore(project).status == adopt.SEEDED
        body = self.read(project)
        assert body.startswith(adopt.GITIGNORE_START)
        assert body.rstrip("\n").endswith(adopt.GITIGNORE_END)
        for line in adopt.GITIGNORE_LINES:
            assert f"\n{line}\n" in body

    def test_a_pnpm_pack_ignores_what_its_install_writes(self, project):
        """A first write runs `pnpm install`, so the directory is there before
        the adopter's first `git status`. One line covers `web/node_modules/`
        too, because git matches the pattern at any depth."""
        for pack in ("typescript", "python+typescript"):
            assert "node_modules/" in adopt.gitignore_block(pack), pack

    def test_a_pack_that_installs_nothing_names_no_node_modules(self, project):
        for pack in ("python", "none"):
            assert "node_modules/" not in adopt.gitignore_block(pack), pack

    def test_the_lockfile_stays_tracked(self, project):
        """CI installs from it, and an ignored lockfile is an install nobody can repeat."""
        assert "pnpm-lock" not in adopt.gitignore_block("typescript")

    def test_the_projects_own_lines_survive(self, project):
        theirs = "node_modules/\n*.log\n"
        (project / ".gitignore").write_text(theirs)
        assert adopt.seed_gitignore(project).status == adopt.APPENDED
        body = self.read(project)
        assert body.startswith(theirs)
        assert adopt.GITIGNORE_START in body

    def test_a_file_with_no_trailing_newline_keeps_its_last_line(self, project):
        (project / ".gitignore").write_text("node_modules/")
        adopt.seed_gitignore(project)
        assert "node_modules/\n" in self.read(project)

    def test_a_rerun_carries_one_block_and_not_two(self, project):
        (project / ".gitignore").write_text("node_modules/\n")
        adopt.seed_gitignore(project)
        assert adopt.seed_gitignore(project).status == adopt.UNCHANGED
        body = self.read(project)
        assert body.count(adopt.GITIGNORE_START) == 1
        assert body.count(".agentkit/local.*") == 1
        assert body.startswith("node_modules/\n")

    def test_a_rerun_over_a_current_block_writes_no_file(self, project):
        adopt.seed_gitignore(project)
        before = (project / ".gitignore").stat().st_mtime_ns
        assert adopt.seed_gitignore(project).status == adopt.UNCHANGED
        assert (project / ".gitignore").stat().st_mtime_ns == before

    def test_an_edit_inside_the_block_comes_back(self, project):
        (project / ".gitignore").write_text(
            f"*.log\n\n{adopt.GITIGNORE_START}\ntheirs/\n{adopt.GITIGNORE_END}\ndist/\n"
        )
        assert adopt.seed_gitignore(project).status == adopt.UPDATED
        body = self.read(project)
        assert "theirs/" not in body
        assert ".agentkit/local.*" in body
        assert body.startswith("*.log\n")
        assert body.endswith("dist/\n")

    def test_a_block_with_no_end_marker_is_left_exactly_as_it_was(self, project):
        """The end marker is where a rewrite stops, so a missing one stops the write."""
        theirs = f"*.log\n{adopt.GITIGNORE_START}\n.agentkit/local.*\n"
        (project / ".gitignore").write_text(theirs)
        assert adopt.seed_gitignore(project).status == adopt.KEPT
        assert self.read(project) == theirs

    def test_a_plan_writes_no_file(self, project):
        assert adopt.plan_gitignore(project).status == adopt.SEEDED
        assert not (project / ".gitignore").exists()

    def test_a_plan_over_an_existing_file_changes_nothing(self, project):
        (project / ".gitignore").write_text("node_modules/\n")
        assert adopt.plan_gitignore(project).status == adopt.APPENDED
        assert self.read(project) == "node_modules/\n"

    def test_it_is_never_in_the_manifest(self, template, project):
        adopt.write(template, project)
        adopt.seed_gitignore(project)
        assert ".gitignore" not in adopt.manifest(project)

    def test_the_report_names_it(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        out = capsys.readouterr().out
        assert "ignore" in out
        assert f"{adopt.SEEDED:<9} .gitignore" in out

    def test_an_unclosed_block_gets_a_paragraph_of_its_own(self, template, project, capsys):
        (project / ".gitignore").write_text(adopt.GITIGNORE_START + "\n")
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert "Put the marker back" in capsys.readouterr().out

    def test_git_ignores_the_personal_layer(self, template, project):
        """The check #48 asks for, put to git rather than to the file's text."""
        import subprocess

        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        env = {"PATH": "/usr/bin:/bin", "HOME": str(project)}
        subprocess.run(["git", "-C", str(project), "init"], check=True, capture_output=True, env=env)
        (project / ".agentkit" / "local.md").write_text("mine\n")
        done = subprocess.run(
            ["git", "-C", str(project), "check-ignore", "-v", ".agentkit/local.md", ".claude/worktrees/"],
            capture_output=True,
            text=True,
            env=env,
        )
        assert done.returncode == 0
        assert ".agentkit/local.*" in done.stdout
        assert ".claude/worktrees/" in done.stdout

    def test_git_ignores_a_generated_artboard(self, template, project):
        """A project runs the generators it was seeded with, and a run writes into `design/`.

        The output is a file the project never wrote, so it stays out of the
        index and the generators beside it stay tracked (#89). `screens.json`
        sits in the same directory as the `canvas.json` a run writes, so the
        layout is named exactly and never as `design/*.json` (#97).
        """
        import subprocess

        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        env = {"PATH": "/usr/bin:/bin", "HOME": str(project)}
        subprocess.run(["git", "-C", str(project), "init"], check=True, capture_output=True, env=env)
        (project / "design").mkdir(exist_ok=True)
        written = ("Home.dc.html", "Home.classes.html", "canvas.json", "build.py", "screens.json")
        for name in written:
            (project / "design" / name).write_text("x\n")

        def ignored(*rels):
            return subprocess.run(
                ["git", "-C", str(project), "check-ignore", *rels],
                capture_output=True,
                text=True,
                env=env,
            )

        done = ignored("design/Home.dc.html", "design/Home.classes.html", "design/canvas.json")
        assert done.returncode == 0
        assert done.stdout.split() == [
            "design/Home.dc.html",
            "design/Home.classes.html",
            "design/canvas.json",
        ]
        kept = ignored("design/build.py", "design/screens.json")
        assert kept.returncode == 1, kept.stdout


class TestAPersonalSkillOfASeededName:
    """The collision `adopt` reports and does not act on (#50).

    Every test points `CLAUDE_CONFIG_DIR` at a directory under `tmp_path`, so
    the personal root under test is a fixture and the real `~/.claude/skills/`
    is never read and never written.
    """

    def personal(self, tmp_path, monkeypatch, *, directory=None, declared=None):
        """A personal skills root holding one skill, and the path to it."""
        home = tmp_path / "home"
        root = home / "skills"
        if directory:
            skill = root / directory
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {declared or directory}\ndescription: A personal copy.\n---\nHello.\n"
            )
        else:
            root.mkdir(parents=True)
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
        return root

    def test_a_personal_skill_of_a_seeded_name_is_named(self, tmp_path, monkeypatch):
        root = self.personal(tmp_path, monkeypatch, directory="demo")
        assert adopt.personal_collisions(FIXTURE) == (root, ["demo"])

    def test_an_empty_personal_root_collides_with_nothing(self, tmp_path, monkeypatch):
        self.personal(tmp_path, monkeypatch)
        assert adopt.personal_collisions(FIXTURE)[1] == []

    def test_a_personal_skill_of_another_name_is_not_a_collision(self, tmp_path, monkeypatch):
        self.personal(tmp_path, monkeypatch, directory="triage")
        assert adopt.personal_collisions(FIXTURE)[1] == []

    def test_the_name_a_personal_skill_declares_is_the_one_that_collides(self, tmp_path, monkeypatch):
        """A `name:` in the frontmatter is what a session types, whatever the directory is called."""
        self.personal(tmp_path, monkeypatch, directory="mine", declared="demo")
        assert adopt.personal_collisions(FIXTURE)[1] == ["demo"]

    def test_a_skill_this_template_does_not_seed_is_not_a_collision(self, tmp_path, monkeypatch, template):
        self.personal(tmp_path, monkeypatch, directory="demo")
        (template / "seeds.json").write_text(json.dumps({"tracked": [STYLE]}))
        assert adopt.personal_collisions(template)[1] == []

    def test_the_personal_root_is_read_and_never_written(self, tmp_path, monkeypatch, template, project):
        root = self.personal(tmp_path, monkeypatch, directory="demo")
        before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert sorted(p.relative_to(root).as_posix() for p in root.rglob("*")) == before

    def test_the_report_names_the_collision_and_the_run_continues(
        self, tmp_path, monkeypatch, template, project, capsys
    ):
        self.personal(tmp_path, monkeypatch, directory="demo")
        assert adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)]) == 0
        out = capsys.readouterr().out
        assert "shadowed  demo" in out
        assert "unreachable by name on this machine" in out
        assert (project / SKILL).is_file()

    def test_the_report_says_so_when_there_is_no_collision(self, tmp_path, monkeypatch, template, project, capsys):
        self.personal(tmp_path, monkeypatch)
        adopt.main([str(project), "--template", str(template)])
        out = capsys.readouterr().out
        assert "no name seeded here is a personal skill" in out
        assert "shadowed" not in out

    def test_a_plan_reports_the_collision_too(self, tmp_path, monkeypatch, template, project, capsys):
        """The plan is where somebody reads what a write would do, so the warning is there."""
        self.personal(tmp_path, monkeypatch, directory="demo")
        adopt.main([str(project), "--template", str(template)])
        assert "shadowed  demo" in capsys.readouterr().out

    def test_a_probe_that_will_not_load_says_so_instead_of_reporting_none(
        self, tmp_path, monkeypatch, template, project, capsys
    ):
        self.personal(tmp_path, monkeypatch, directory="demo")
        monkeypatch.setattr(adopt, "PROBE_REL", "probes/gone.py")
        assert adopt.personal_collisions(template) == (None, [])
        adopt.main([str(project), "--template", str(template)])
        assert "did not load, so no personal skill was listed" in capsys.readouterr().out


class TestTheProjectCommand:
    """The command named after the project, where a session starts.

    #146 settled reading 2 of four: it reads the layers and the phase, then
    says where the last session stopped. `/work` reads the board. Rendered per
    project like `CLAUDE.md` and the two workflows, so it carries no manifest
    row and no rerun replaces it.
    """

    def test_a_name_with_a_space_and_a_capital_becomes_a_slug(self):
        assert adopt.command_name("Mac Hours") == "mac-hours"
        assert adopt.command_name("  CSS Fun / Experiments!  ") == "css-fun-experiments"
        assert adopt.command_name("agentkit") == "agentkit"

    def test_a_name_with_no_letter_or_digit_names_no_command(self):
        assert adopt.command_name("...") == ""

    def test_it_falls_back_to_the_directory_name(self, template, project):
        slug, why = adopt.project_command(template, project, {**ANSWERS, "name": "***"})
        assert (slug, why) == ("project", "")

    def test_a_name_that_survives_neither_seeds_nothing_and_says_why(self, template, tmp_path):
        odd = tmp_path / "***"
        odd.mkdir()
        slug, why = adopt.project_command(template, odd, {**ANSWERS, "name": "***"})
        assert slug == ""
        assert "names no command" in why

    def test_a_name_matching_a_seeded_command_is_refused(self, project):
        """`.claude/commands/` is a byte copy replaced on every rerun, so a rendered
        file written there would be overwritten and the project would lose its entry
        point without being told.
        """
        slug, why = adopt.project_command(ROOT, project, {**ANSWERS, "name": "Work"})
        assert slug == ""
        assert "already seeds" in why

    def test_it_lands_in_an_empty_project(self, template, project):
        rows = adopt.seed_command(project, ANSWERS, "demo")
        assert statuses(rows) == {".claude/commands/demo.md": "seeded"}
        assert (project / ".claude/commands/demo.md").is_file()

    def test_the_body_reads_the_layers_and_the_phase(self, template, project):
        adopt.seed_command(project, ANSWERS, "demo")
        body = (project / ".claude/commands/demo.md").read_text()
        assert "session on demo starts" in body
        assert "`.agentkit/phase.json`" in body
        assert "`.agentkit/team.md`" in body
        assert "CLAUDE.md" in body

    def test_shaping_names_shape_and_building_names_work(self, project):
        """A project in `shaping` has no board, and `pick-work` says as much."""
        adopt.seed_command(project, ANSWERS, "demo")
        body = (project / ".claude/commands/demo.md").read_text()
        assert "**`shaping`.**" in body and "`shape` skill" in body
        assert "**`building`.**" in body and "`/work`" in body

    def test_only_shaping_says_the_tree_carries_no_intent(self, project):
        """#184: a session read a framework-less `package.json` in a SvelteKit app and
        reported the seeded gates were wrong for a static-CSS repository. `building`
        reads the board, which states intent, so the sentence lands in one branch.
        """
        adopt.seed_command(project, ANSWERS, "demo")
        body = (project / ".claude/commands/demo.md").read_text()
        shaping, _, building = body.partition("**`building`.**")
        assert "never what is intended" in shaping
        assert "question for the operator" in shaping
        assert "what is intended" not in building

    def test_the_frontmatter_carries_the_slug_and_never_the_raw_name(self, project):
        """A project name may hold a quote or a colon, and the slug never can."""
        adopt.seed_command(project, {**ANSWERS, "name": 'Bob"s: thing'}, "bob-s-thing")
        front = (project / ".claude/commands/bob-s-thing.md").read_text().split("---")[1]
        assert "bob-s-thing" in front
        assert '"' not in front and ":" in front.split("description")[1][:2]

    def test_a_rerun_leaves_an_edited_command_alone(self, project):
        adopt.seed_command(project, ANSWERS, "demo")
        (project / ".claude/commands/demo.md").write_text("# ours\n")
        rows = adopt.seed_command(project, ANSWERS, "demo")
        assert statuses(rows) == {".claude/commands/demo.md": "present"}
        assert (project / ".claude/commands/demo.md").read_text() == "# ours\n"

    def test_it_is_never_in_the_manifest(self, template, project):
        adopt.write(template, project)
        adopt.seed_command(project, ANSWERS, "demo")
        assert not any(rel.endswith("/demo.md") for rel in adopt.manifest(project))

    def test_a_plan_writes_no_command(self, project):
        assert statuses(adopt.plan_command(project, "demo")) == {".claude/commands/demo.md": "seeded"}
        assert not (project / ".claude/commands").exists()

    def test_a_refused_slug_plans_nothing(self, project):
        assert adopt.plan_command(project, "") == []

    def test_a_write_seeds_it_and_the_report_names_it(self, template, project, capsys):
        assert adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)]) == 0
        out = capsys.readouterr().out
        assert "the entry point a session starts at" in out
        assert (project / ".claude/commands/project.md").is_file()

    def test_the_router_names_it_as_the_entry_point(self, template):
        body = adopt.router(template, ANSWERS, "demo")
        assert "`/demo` is where a session starts" in body
        assert "`/work`, reads the board" in body

    def test_the_router_names_work_alone_when_there_is_no_command(self, template):
        body = adopt.router(template, ANSWERS, "")
        assert "/demo" not in body
        assert "`/work`" in body

    def test_no_placeholder_survives_either_rendering(self, template):
        for slug in ("demo", ""):
            assert not re.search(r"\{[a-z_]+\}", adopt.router(template, ANSWERS, slug))

    def test_both_files_say_which_one_reads_the_board(self, project):
        """Or the second is dead weight the moment somebody notices they overlap."""
        adopt.seed_command(project, ANSWERS, "demo")
        assert "reads the board" in (project / ".claude/commands/demo.md").read_text()
        assert "reads the board" in (ROOT / ".claude/commands/work.md").read_text()


class TestTheEffortLabels:
    """The three `effort:` labels a first write creates, and the areas it does not.

    #125 settled position 2: effort describes what it costs to verify
    something and reads the same in any project, areas are the project's own
    and `shape` settles them. `gh` is never called here; every test drives the
    two subprocess helpers, so the suite touches no remote.
    """

    @pytest.fixture
    def gh(self, monkeypatch):
        """A recorder standing in for `gh`, with one label already on the board."""
        calls: list[tuple[str, ...]] = []
        existing = ['{"name": "effort: quick"}', '{"name": "bug"}']

        def fake_git(root, *args):
            return subprocess.CompletedProcess(args, 0, stdout="origin\n", stderr="")

        def fake_gh(root, *args):
            calls.append(args)
            if args[:2] == ("label", "list"):
                return subprocess.CompletedProcess(args, 0, stdout=f"[{','.join(existing)}]", stderr="")
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        monkeypatch.setattr(adopt, "_git", fake_git)
        monkeypatch.setattr(adopt, "_gh", fake_gh)
        return calls

    def test_it_creates_the_two_that_are_missing(self, project, gh):
        rows, problem = adopt.seed_labels(project)
        assert problem == ""
        assert statuses(rows) == {
            "effort: quick": "present",
            "effort: session": "seeded",
            "effort: blocked": "seeded",
        }

    def test_a_rerun_over_a_full_board_creates_nothing(self, project, monkeypatch):
        monkeypatch.setattr(
            adopt, "_git", lambda root, *a: subprocess.CompletedProcess(a, 0, stdout="origin\n", stderr="")
        )
        board = json.dumps([{"name": name} for name, _, _ in adopt.EFFORT_LABELS])
        monkeypatch.setattr(
            adopt, "_gh", lambda root, *a: subprocess.CompletedProcess(a, 0, stdout=board, stderr="")
        )
        rows, problem = adopt.seed_labels(project)
        assert problem == ""
        assert {row.status for row in rows} == {"present"}

    def test_it_creates_no_area_label(self, project, gh):
        adopt.seed_labels(project)
        created = [args for args in gh if args[:2] == ("label", "create")]
        assert created
        assert not [args for args in created if args[2].startswith("area:")]

    def test_every_label_carries_a_description_and_a_colour(self, project, gh):
        adopt.seed_labels(project)
        for args in [a for a in gh if a[:2] == ("label", "create")]:
            assert "--description" in args and "--color" in args

    def test_the_descriptions_are_about_verification_cost(self):
        """They transfer because none of them names agentkit or any project part."""
        assert [name for name, _, _ in adopt.EFFORT_LABELS] == [
            "effort: quick",
            "effort: session",
            "effort: blocked",
        ]
        for _, description, colour in adopt.EFFORT_LABELS:
            assert description and re.fullmatch(r"[0-9a-f]{6}", colour)

    def test_a_project_with_no_remote_is_reported_and_nothing_runs(self, project, monkeypatch):
        monkeypatch.setattr(adopt, "_git", lambda root, *a: None)
        called = []
        monkeypatch.setattr(adopt, "_gh", lambda root, *a: called.append(a))
        rows, problem = adopt.seed_labels(project)
        assert rows == [] and "no git remote" in problem
        assert called == []

    def test_a_machine_with_no_gh_is_reported(self, project, monkeypatch):
        monkeypatch.setattr(
            adopt, "_git", lambda root, *a: subprocess.CompletedProcess(a, 0, stdout="origin\n", stderr="")
        )
        monkeypatch.setattr(adopt, "_gh", lambda root, *a: None)
        rows, problem = adopt.seed_labels(project)
        assert rows == [] and "no gh" in problem

    def test_an_unauthenticated_gh_is_reported_on_one_line(self, project, monkeypatch):
        monkeypatch.setattr(
            adopt, "_git", lambda root, *a: subprocess.CompletedProcess(a, 0, stdout="origin\n", stderr="")
        )
        monkeypatch.setattr(
            adopt,
            "_gh",
            lambda root, *a: subprocess.CompletedProcess(a, 1, stdout="", stderr="gh: not logged in\nrun gh auth login\n"),
        )
        rows, problem = adopt.seed_labels(project)
        assert rows == [] and problem == "gh: not logged in"

    def test_a_failed_create_stops_and_keeps_what_landed(self, project, monkeypatch):
        monkeypatch.setattr(
            adopt, "_git", lambda root, *a: subprocess.CompletedProcess(a, 0, stdout="origin\n", stderr="")
        )

        def fake_gh(root, *args):
            if args[:2] == ("label", "list"):
                return subprocess.CompletedProcess(args, 0, stdout="[]", stderr="")
            if args[2] == "effort: quick":
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="HTTP 403\n")

        monkeypatch.setattr(adopt, "_gh", fake_gh)
        rows, problem = adopt.seed_labels(project)
        assert statuses(rows) == {"effort: quick": "seeded"}
        assert problem == "HTTP 403"

    def test_a_first_write_reaches_them_and_a_rerun_does_not(self, template, project, capsys):
        assert adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)]) == 0
        assert "no git remote" in capsys.readouterr().out
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert "not a first write, so no label was read or created" in capsys.readouterr().out

    def test_the_flag_skips_it(self, template, project, capsys):
        adopt.main([str(project), "--write", "--pack", "none", "--no-labels", "--template", str(template)])
        assert "not a first write, so no label was read or created" in capsys.readouterr().out

    def test_a_plan_says_what_a_first_write_would_create(self, template, project, capsys):
        adopt.main([str(project), "--template", str(template)])
        assert "a first write creates them and no area: label" in capsys.readouterr().out

    def test_the_report_names_shape_and_the_directory_it_runs_in(self, template, project, capsys):
        """#128: a next step with no directory on it gets run in the wrong repository."""
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        out = capsys.readouterr().out
        assert "No area: label was created" in out
        assert "`shape` settles them" in out
        assert f"Run `shape` in {project}" in out
        assert "`.agentkit/process.toml`\nstays unwritten" in out

    def test_the_labels_never_reach_the_agentkit_checkout(self, template, project, monkeypatch):
        """gh reads the working directory's remote, so a call from here files against agentkit."""
        seen = []
        monkeypatch.setattr(
            adopt, "_git", lambda root, *a: subprocess.CompletedProcess(a, 0, stdout="origin\n", stderr="")
        )

        def fake_gh(root, *args):
            seen.append(Path(root))
            return subprocess.CompletedProcess(args, 0, stdout="[]", stderr="")

        monkeypatch.setattr(adopt, "_gh", fake_gh)
        adopt.seed_labels(project)
        assert seen and set(seen) == {project}
