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
on purpose, so its assertion is the strict one: every status the script
declares has a row, and no row names one the script cannot report. The statuses
are read off the imported module, because a parse of the file saw only the
shapes its author had met and passed while `appended` was missing (#70).
"""

from __future__ import annotations

import importlib.util
import re
import sys
from importlib.machinery import SourceFileLoader
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


def _adopt():
    """`bin/adopt` as a module. It carries no extension, so a plain import misses it.

    `tests/test_adopt.py` loads it the same way under the same name. Whichever
    file runs first does the work and the other reads what is there, so one
    module object stands behind the one `sys.modules` entry.
    """
    if "adopt" in sys.modules:
        return sys.modules["adopt"]
    loader = SourceFileLoader("adopt", str(ADOPT))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader("adopt", loader))
    # Registered before it runs, because `@dataclass` resolves annotations
    # through `sys.modules[cls.__module__]` and a module absent from there raises.
    sys.modules["adopt"] = module
    loader.exec_module(module)
    return module


def _reported_outcomes() -> set[str]:
    """Every status `bin/adopt` declares, read off the imported module.

    A status constant spells its own value, `APPENDED = "appended"`, and no
    other module level string in that file holds its own name: the rest are
    paths, markers and rendered bodies.

    Reading the module replaces a parse of it. A parser has to resolve the
    argument `Outcome` was built with, and a status reaches it as a local
    unpacked from `gitignore(...)` and as the subscript `gitignore(...)[1]`,
    so the two shapes nobody had thought of hid `appended` while the test
    passed (#70). What this costs is one direction of precision: a status
    constant nothing ever passes to `Outcome` still needs its row.
    """
    return {
        value
        for name, value in vars(_adopt()).items()
        if isinstance(value, str) and name == value.upper()
    }


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


# ---------------------------------------------------------------------------
# A skill's `description` against the step count in its own body


# The frontmatter is one `key: value` per line and the loader reads
# `description` out of it. The parser stops at the next key, so a description
# that wrapped onto a second line is read whole and the guard below fails
# loudly instead of matching half a sentence.
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
DESCRIPTION = re.compile(r"^description:(.*?)(?=^[a-z][a-z0-9_-]*:|\Z)", re.M | re.S)

# The numbered headings a body walks through. `## Preconditions` is not one.
STEP_HEADING = re.compile(r"^## \d+\.")

# A fenced block, opened and closed by three or more backticks or tildes, up to
# three spaces in. `shape` renders an example router inside one, and both of the
# `## N.` lines it shows belong to the example.
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")

# Spelled out because a description says "five" where a heading says `5.`, and
# both spellings make the same claim about the same file. `one` is in the list
# and costs a description the pronoun: "where the next one can start" reads as
# a count of one. STYLE.md's `## Required` asks for the noun there anyway.
NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}
NUMBER = re.compile(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\b", re.I)


def _skill_text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def _description(text: str) -> str:
    front = FRONTMATTER.match(text)
    if not front:
        return ""
    found = DESCRIPTION.search(front.group(1) + "\n")
    return " ".join(found.group(1).split()) if found else ""


def _claimed_numbers(description: str) -> list[int]:
    return [
        int(found) if found.isdigit() else NUMBER_WORDS[found.lower()]
        for found in NUMBER.findall(description)
    ]


def _steps(text: str) -> int:
    """The `## N.` headings a body walks through, counting none inside a fence.

    A skill that renders a numbered document as an example has those numbers in
    its body without walking through them. Counted over the whole text, `shape`
    has two steps it does not have, and a description stating its real count
    would be the thing that failed (#70).

    A closing fence matches the character its opening used and runs at least as
    long, so a ```` ``` ```` inside a four-backtick block closes nothing.
    """
    steps = 0
    fence = ""
    for line in text.splitlines():
        if found := FENCE.match(line):
            marker = found.group(1)
            if not fence:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = ""
        elif not fence and STEP_HEADING.match(line):
            steps += 1
    return steps


def _miscounts(description: str, steps: int) -> list[int]:
    """Every number a description states that the body's step count contradicts."""
    return [n for n in _claimed_numbers(description) if n != steps]


DESCRIBED = {name: _description(_skill_text(name)) for name in sorted(PRESENT)}
STEPS = {name: _steps(_skill_text(name)) for name in sorted(PRESENT)}


def test_every_skill_has_a_description_and_some_carry_steps() -> None:
    """Two extractions that matched nothing would agree with everything."""
    empty = sorted(name for name, text in DESCRIBED.items() if not text)
    assert not empty, f"no `description` read out of {empty}; the frontmatter shape changed"
    assert any(STEPS.values()), "no `## N.` heading read anywhere; the heading shape changed"


def test_no_description_states_a_step_count_its_body_contradicts() -> None:
    """The drift #44 measured: two descriptions counted their own body wrong.

    `design-process` said seven phases over a body of nine steps, and `wrap-up`
    said three over five. A description is what the loader shows, and #34 left
    it standing in place of the list `CLAUDE.md` used to carry, so a wrong
    count there is read every session and corrected by nobody.

    A count is arithmetic and no judgment about phrasing, which keeps this
    clear of STYLE.md's argument against a checker that guesses. It lives here
    rather than in `bin/check-style` because that gate reads one line at a time
    and ships into every adopted project, where `## N.` means whatever that
    project's skills mean by it.
    """
    wrong = {
        name: (claimed, STEPS[name])
        for name, description in DESCRIBED.items()
        if (claimed := _miscounts(description, STEPS[name]))
    }
    assert not wrong, (
        f"a description names a number its body does not have, as "
        f"name: (claimed, `## N.` headings): {wrong}"
    )


# A body carrying both kinds of `## N.`: two headings the skill walks through,
# and two inside a fenced example of a document it renders. `shape` is the real
# case, and a fixture keeps this guard still while that skill's body moves.
FENCED_EXAMPLE = """---
name: demo
description: Two steps, and an example of the numbering they write.
---

# Demo

## 1. Ask

What the answer lands as:

```markdown
## 1. The constraint, stated as what holds

## 2. The next one
```

## 2. Write
"""


def test_a_numbered_example_inside_a_fence_is_not_a_step() -> None:
    """A skill may render a numbered document without walking through it.

    Four `## N.` lines, two of them the example's. Counting all four rejects
    the description for stating the truth, which is what `shape` would have hit
    the moment its description carried a number (#70).
    """
    assert len(re.findall(r"^## \d+\.", FENCED_EXAMPLE, re.M)) == 4
    assert _steps(FENCED_EXAMPLE) == 2
    assert not _miscounts(_description(FENCED_EXAMPLE), _steps(FENCED_EXAMPLE))
