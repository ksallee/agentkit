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

# The six answers, as `main` assembles them. One constant, because the router
# and the team layer are rendered from the same dict.
ANSWERS = {
    "pack": "python",
    "name": "demo",
    "summary": "A project.",
    "phase": "building",
    "merge": "Both of us review.",
    "references": "curated",
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

    def test_the_references_answer_reaches_the_team_file(self, project):
        adopt.seed_team(project, {**ANSWERS, "references": "refero"})
        body = (project / ".agentkit" / "team.md").read_text()
        assert "| references | curated, refero |" in body
        assert "`references` is `refero`" in body

    def test_surface_is_seeded_unanswered(self, project):
        adopt.seed_team(project, ANSWERS)
        body = (project / ".agentkit" / "team.md").read_text()
        assert "| surface | canvas, file, none |" in body
        assert "`surface` waits until somebody picks one." in body

    def test_the_command_defaults_references_to_curated(self, template, project):
        adopt.main([str(project), "--write", "--pack", "none", "--template", str(template)])
        assert "`references` is `curated`" in (project / ".agentkit" / "team.md").read_text()

    def test_every_heading_this_repository_uses_is_one_adopt_writes(self, project):
        """One direction of #26, and it is the direction that broke.

        `.agentkit/team.md` here is hand-written and `team_files()` renders the
        seeded copy, so a section added to this repository's file and not to the
        renderer gives every adopted project a team layer missing it. The other
        direction stays open while the design section lands on two branches.
        """
        ours = re.findall(r"^## (.+)$", (ROOT / ".agentkit" / "team.md").read_text(), re.M)
        seeded = re.findall(r"^## (.+)$", adopt.team_files(ANSWERS)["team.md"], re.M)
        assert set(ours) - set(seeded) == set()


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

    def test_rules_1_to_8_carry_no_constraint_and_nothing_to_fill_in(self, template):
        """An empty heading invites a guess and a question list invites an answer."""
        section = adopt.router(template, ANSWERS).split("## 1 to 8")[1].split("\n## ")[0]
        assert "?" not in section
        assert "- " not in section
        assert "TODO" not in section


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
