"""What `CLAUDE.md` may say about `.claude/skills/`, and what it may not.

`CLAUDE.md` used to name every skill. The list drifted twice in two days, at
#31 and #34, because a skill lands in its own directory and nothing makes the
router notice. Every `SKILL.md` already opens with a `description` written to
be read at load time, so the list was that description again in a file with no
way to know a skill arrived.

What is asserted here is the pair that stays load-bearing. A slash command is
the one thing a `description` cannot advertise, so `CLAUDE.md` names the skills
that have one, and a command whose skill went missing is a broken instruction.
Nothing asserts that every skill is named, because the point of the change is
that most are not.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "CLAUDE.md"
SKILLS = ROOT / ".claude" / "skills"
COMMANDS = ROOT / ".claude" / "commands"

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
