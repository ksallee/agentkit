"""The scaffolding a project adopted holds together, checked from inside it.

    uv run pytest tests/test_scaffolding.py

agentkit seeds this file into a project whose pack declares `uv run pytest`, so
that gate collects something on its first run and the green says the
scaffolding is sound instead of saying the directory was empty. It is also
where a project's own tests go: write them beside it, and this file stays as
the one agentkit replaces on a rerun. `tests/scaffolding.test.mjs` is its twin,
seeded to a pack that declares `pnpm test`.

Everything here reads the team layer and `bin/`, which every adopted project
has. Nothing here runs a gate. `bin/verify` runs the gates, and one of them
runs this file.
"""

from __future__ import annotations

import stat
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATES = ROOT / ".agentkit" / "gates.toml"
TEAM = ROOT / ".agentkit" / "team.md"
ROUTER = ROOT / "CLAUDE.md"


def declared() -> list[dict]:
    """Every gate `.agentkit/gates.toml` declares, in order."""
    return tomllib.loads(GATES.read_text(encoding="utf-8")).get("gate", [])


class TestTheTeamLayer:
    """Rule 0's committed layer, and the router an agent loads from the root."""

    def test_the_gate_declaration_parses(self):
        assert GATES.is_file(), f"{GATES} is absent, so rule 17 has nothing to run"
        declared()

    def test_every_gate_names_itself_and_a_command(self):
        for n, gate in enumerate(declared(), 1):
            assert gate.get("name"), f"gate {n} declares no name"
            assert gate.get("command"), f"gate {gate.get('name', n)} declares no command"

    def test_no_gate_name_is_declared_twice(self):
        names = [gate["name"] for gate in declared()]
        assert len(names) == len(set(names)), names

    def test_the_team_layer_carries_something(self):
        assert TEAM.is_file(), ".agentkit/team.md is absent, so rule 0 has no team layer"
        assert TEAM.read_text(encoding="utf-8").strip()

    def test_the_router_is_at_the_root(self):
        assert ROUTER.is_file(), "an agent loads CLAUDE.md from the root and finds none"


class TestTheCheckersTheGatesName:
    """A gate naming `bin/x` fails at the runner when that file went missing.

    `bin/verify` splits a command with shlex and runs it without a shell, so an
    absent or unreadable checker reports as a FileNotFoundError under a gate
    name and says nothing about which file to put back.
    """

    @staticmethod
    def checkers() -> list[str]:
        first = [gate["command"].split()[0] for gate in declared()]
        return sorted({token for token in first if token.startswith("bin/")})

    def test_a_gate_names_one(self):
        assert self.checkers(), "no gate runs a seeded checker, so this class checks nothing"

    def test_each_one_is_here_and_executable(self):
        for rel in self.checkers():
            path = ROOT / rel
            assert path.is_file(), f"{rel} is declared as a gate command and is not here"
            assert path.stat().st_mode & stat.S_IXUSR, f"{rel} is here and is not executable"
