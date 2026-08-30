"""The rule 21 registry, and the skill that writes it.

`bin/surface` is the mechanism `/done` has instead of a checklist: a surface
written and left unrecorded is one the next session cannot route to. What is
asserted here is that a row is trustworthy (the file exists, one name is one
row), that a registry it cannot parse is never silently blanked, and that the
path it writes to stays covered by `.gitignore`.

Nothing asserts the wording of the skill. Two facts about it are checked: it
names the registry command, and it carries no other project's vocabulary.
"""

from __future__ import annotations

import json
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "bin" / "surface"
SKILL = ROOT / ".claude" / "skills" / "wrap-up" / "SKILL.md"
COMMAND = ROOT / ".claude" / "commands" / "done.md"
REGISTRY_REL = ".agentkit/local.surfaces.json"


def load(path: Path):
    """Import an extensionless executable, which cannot be imported by name."""
    loader = SourceFileLoader(path.name.replace("-", "_"), str(path))
    module = module_from_spec(spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SURFACE), *args], capture_output=True, text=True, cwd=ROOT
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A root with one file worth recording, and no registry yet."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "GUIDE.md").write_text("A surface.\n", encoding="utf-8")
    return tmp_path


def registry(project: Path) -> dict:
    return json.loads((project / REGISTRY_REL).read_text(encoding="utf-8"))


class TestRecording:
    def test_a_recorded_surface_is_listed(self, project):
        done = run("--root", str(project), "record", "guide", "docs/GUIDE.md")
        assert done.returncode == 0, done.stderr
        listed = run("--root", str(project), "list")
        assert "guide" in listed.stdout
        assert "docs/GUIDE.md" in listed.stdout

    def test_one_name_is_one_row(self, project):
        run("--root", str(project), "record", "guide", "docs/GUIDE.md")
        first = registry(project)["surfaces"]["guide"]["written_at"]
        run("--root", str(project), "record", "guide", "docs/GUIDE.md")
        rows = registry(project)["surfaces"]
        assert list(rows) == ["guide"]
        assert rows["guide"]["written_at"] >= first

    def test_a_name_that_is_not_a_slug_is_refused(self, project):
        done = run("--root", str(project), "record", "Guide Doc", "docs/GUIDE.md")
        assert done.returncode != 0
        assert not (project / REGISTRY_REL).exists()

    def test_a_surface_that_does_not_exist_is_refused(self, project):
        """A row pointing at nothing makes every other row untrustworthy."""
        done = run("--root", str(project), "record", "ghost", "docs/GONE.md")
        assert done.returncode != 0
        assert "docs/GONE.md" in done.stderr + done.stdout
        assert not (project / REGISTRY_REL).exists()

    def test_a_surface_inside_the_root_is_stored_relative(self, project):
        run("--root", str(project), "record", "guide", "docs/GUIDE.md")
        assert registry(project)["surfaces"]["guide"]["path"] == "docs/GUIDE.md"

    def test_a_surface_outside_the_root_keeps_its_whole_path(self, project, tmp_path):
        """The personal layer may sit outside the checkout (#15)."""
        outside = tmp_path.parent / "elsewhere.md"
        outside.write_text("Taste.\n", encoding="utf-8")
        run("--root", str(project), "record", "personal", str(outside))
        stored = Path(registry(project)["surfaces"]["personal"]["path"])
        assert stored.is_absolute()
        assert stored.resolve() == outside.resolve()


class TestReading:
    def test_an_absent_registry_is_a_fresh_checkout(self, project):
        done = run("--root", str(project), "list")
        assert done.returncode == 0
        assert "No surfaces recorded" in done.stdout

    def test_a_surface_that_has_gone_is_marked(self, project):
        run("--root", str(project), "record", "guide", "docs/GUIDE.md")
        (project / "docs" / "GUIDE.md").unlink()
        done = run("--root", str(project), "list")
        assert "MISSING" in done.stdout

    @pytest.mark.parametrize(
        "command", (("list",), ("record", "guide", "docs/GUIDE.md")), ids=("list", "record")
    )
    def test_a_registry_it_cannot_parse_is_never_blanked(self, project, command):
        """Rewriting a corrupt file would drop rows with nobody told."""
        (project / ".agentkit").mkdir()
        broken = project / REGISTRY_REL
        broken.write_text("{ not json", encoding="utf-8")
        done = run("--root", str(project), *command)
        assert done.returncode != 0
        assert broken.read_text(encoding="utf-8") == "{ not json"

    def test_a_json_file_that_is_not_a_registry_is_refused(self, project):
        (project / ".agentkit").mkdir()
        (project / REGISTRY_REL).write_text('{"version": 1}', encoding="utf-8")
        done = run("--root", str(project), "list")
        assert done.returncode != 0


class TestWhereItWrites:
    def test_the_registry_path_is_ignored_by_git(self):
        """`.gitignore` reserves `.agentkit/local.*`, and the registry relies on it."""
        surface = load(SURFACE)
        for rel in (surface.REGISTRY_REL, surface.REGISTRY_REL.replace(".json", ".tmp")):
            done = subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT)
            assert done.returncode == 0, f"{rel} would be committed"

    def test_a_worktree_and_its_checkout_share_one_registry(self, tmp_path):
        """`wrap-up` deletes worktrees, so a registry inside one goes with it."""
        surface = load(SURFACE)
        main = tmp_path / "main"
        main.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=main, check=True)
        (main / "seed.txt").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=main, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed"],
            cwd=main,
            check=True,
        )
        linked = tmp_path / "linked"
        subprocess.run(["git", "worktree", "add", "-q", str(linked), "-b", "side"], cwd=main)
        assert surface.repository_root(linked).resolve() == main.resolve()


class TestTheSkill:
    def test_the_loop_closes(self):
        """A project gets `/done`, or a session has no way to end properly."""
        tracked = json.loads((ROOT / "seeds.json").read_text())["tracked"]
        assert "bin/surface" in tracked
        assert SKILL.is_file()
        assert COMMAND.is_file()
        assert "wrap-up" in COMMAND.read_text(encoding="utf-8")

    def test_it_names_the_registry(self):
        """Without the registry it is a checklist, which is what #11 refused."""
        assert "bin/surface record" in SKILL.read_text(encoding="utf-8")

    def test_it_carries_no_other_project_vocabulary(self):
        skill = SKILL.read_text(encoding="utf-8")
        for borrowed in ("hours state", "mac-hours", "context.md", "aw-server", "DESIGNER.md"):
            assert borrowed not in skill, f"wrap-up names {borrowed}"

    def test_it_routes_to_the_layers_rule_0_declares(self):
        skill = SKILL.read_text(encoding="utf-8")
        for layer in (".agentkit/team.md", ".agentkit/local.md", "CLAUDE.md"):
            assert layer in skill
