"""What a document may claim about `.claude/skills/`, and what a skill may claim
about the code it drives.

`CLAUDE.md` used to name every skill. The list drifted twice in two days, at
#31 and #34, because a skill lands in its own directory and nothing makes the
router notice. Every `SKILL.md` already opens with a `description` written to
be read at load time, so the list was that description again in a file with no
way to know a skill arrived.

What is asserted about the router is the pair that stays load-bearing. A slash
command is the one thing a `description` cannot advertise, so `CLAUDE.md` names
the skills that have one, and a command whose skill went missing is a broken
instruction. Nothing asserts that every skill is named, because the point of
the change is that most are not.

The `adopt` skill tables the outcomes `bin/adopt` prints, and #41 added
`removed` and `orphaned` while the table stayed at four. That table enumerates
on purpose, so its assertion is the strict one: every status the script can put
on an `Outcome` has a row, and no row names one it cannot.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "CLAUDE.md"
SKILLS = ROOT / ".claude" / "skills"
COMMANDS = ROOT / ".claude" / "commands"
ADOPT = ROOT / "bin" / "adopt"
ADOPT_SKILL = SKILLS / "adopt" / "SKILL.md"

ROUTER_TEXT = ROUTER.read_text(encoding="utf-8")

# A skill is cited as `name` in bold: **`pick-work`**. Plain backticks are not
# enough, because the prose cites `.claude/skills/` and `SKILL.md` too.
CITED = set(re.findall(r"\*\*`([a-z][a-z0-9-]*)`\*\*", ROUTER_TEXT))

PRESENT = {d.name for d in SKILLS.iterdir() if (d / "SKILL.md").is_file()}
COMMANDED = {f.stem for f in COMMANDS.glob("*.md")}


def test_router_cites_at_least_one_skill() -> None:
    """A regex that silently matches nothing would pass every other test."""
    assert CITED, f"no skill cited in {ROUTER.name}; the citation form changed"


def test_every_cited_skill_exists() -> None:
    """`CLAUDE.md` is an instruction. Naming a skill that is gone misroutes."""
    missing = sorted(CITED - PRESENT)
    assert not missing, f"{ROUTER.name} names skills that do not exist: {missing}"


def test_every_command_names_a_skill_that_exists() -> None:
    """`/work` with no `pick-work` behind it is a command that cannot run."""
    for command in sorted(COMMANDED):
        body = (COMMANDS / f"{command}.md").read_text(encoding="utf-8")
        named = set(re.findall(r"`?([a-z][a-z0-9-]*)`?", body)) & PRESENT
        assert named, f"/{command} names no skill under .claude/skills/"


def test_commanded_skills_are_cited_in_the_router() -> None:
    """The one fact a `description` cannot carry is that a command exists."""
    commanded_skills = {
        skill
        for skill in PRESENT
        for command in COMMANDED
        if skill in (COMMANDS / f"{command}.md").read_text(encoding="utf-8")
    }
    uncited = sorted(commanded_skills - CITED)
    assert not uncited, (
        f"{ROUTER.name} does not name skills that have a slash command: {uncited}"
    )


def test_the_router_does_not_list_every_skill() -> None:
    """The regression this file exists for. A full list drifts, twice measured.

    If somebody restores the list, this fails and points at #34 rather than
    letting it rot until a third issue is filed.
    """
    assert CITED != PRESENT, (
        f"{ROUTER.name} names every skill again. That list drifted at #31 and "
        f"#34; a `description` is read at load time and this file is not."
    )


# ---------------------------------------------------------------------------
# The `adopt` skill's outcome table against the statuses `bin/adopt` reports


def _reported_outcomes() -> set[str]:
    """Every status `bin/adopt` can put on an `Outcome`, read out of its source.

    The script carries no extension and is run rather than imported, so this
    parses it. A status reaches the operator only as `Outcome`'s second
    argument, which is where the names come from: a constant nothing passes
    there is a name the script cannot report, and a name added there arrives
    here with no edit.
    """
    tree = ast.parse(ADOPT.read_text(encoding="utf-8"))
    constants = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
        for target in node.targets
        if isinstance(target, ast.Name) and isinstance(node.value.value, str)
    }
    named: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Outcome":
            status = node.args[1] if len(node.args) > 1 else _keyword(node, "status")
            named |= _names(status)
    return {constants[name] for name in named if name in constants}


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    return next((kw.value for kw in call.keywords if kw.arg == name), None)


def _names(node: ast.expr | None) -> set[str]:
    """The names one status argument can evaluate to.

    An `IfExp` picks between two of them and its test names a path, so taking
    every name under the node would read `ROUTER_REL` as a status.
    """
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, ast.IfExp):
        return _names(node.body) | _names(node.orelse)
    return set()


def _tabled_outcomes() -> set[str]:
    """Every outcome named in the skill, as the first cell of a row.

    A table qualifies by its header cell reading `Outcome`. The skill holds six
    other tables, and scanning them all would read a preconditions row or an
    excuse as a status name.
    """
    out: set[str] = set()
    in_table = False
    for line in ADOPT_SKILL.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            in_table = False
            continue
        cell = line.split("|")[1].strip()
        if cell == "Outcome":
            in_table = True
        elif in_table and (found := re.fullmatch(r"`([a-z][a-z0-9-]*)`", cell)):
            out.add(found.group(1))
    return out


REPORTED = _reported_outcomes()
TABLED = _tabled_outcomes()


def test_outcome_names_are_readable_from_both_sides() -> None:
    """Two extractions that silently matched nothing would agree on nothing."""
    assert REPORTED, f"no status read out of {ADOPT}; `Outcome` is built another way now"
    assert TABLED, f"no outcome row read out of {ADOPT_SKILL}; the table shape changed"


def test_every_reported_outcome_is_tabled() -> None:
    """The drift #58 found: #41 added two statuses and the table stayed at four."""
    missing = sorted(REPORTED - TABLED)
    assert not missing, f"bin/adopt reports outcomes the skill does not table: {missing}"


def test_no_tabled_outcome_is_unreportable() -> None:
    """A row for a status nothing prints sends the operator looking for it."""
    extra = sorted(TABLED - REPORTED)
    assert not extra, f"the skill tables outcomes bin/adopt cannot report: {extra}"
