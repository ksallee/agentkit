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
        assert statuses(results) == {rel: adopt.WRITTEN for rel in ALL_SEEDED}
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
        return {
            "pack": "python",
            "name": "demo",
            "summary": "A project.",
            "phase": "building",
            "merge": "Both of us review.",
        }

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
        assert [g["run"] for g in parsed.get("gate", [])] == [run for _, run in adopt.PACKS[pack]]

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
