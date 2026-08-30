#!/usr/bin/env python3
"""Print the roots Claude Code loads skills from, and every name that sits in two of them.

    python3 probes/skill_precedence.py
    python3 probes/skill_precedence.py --project ../other-repo

Rule 9. `CLAUDE.md` closes with "two skills of one name both load" and nothing
measured it. Claude Code's skill loader is the external interface: it reads
three roots on the machine it runs on, concatenates them and hands one list to
the session. A project that seeds `pick-work` into somebody who already has a
personal skill of that name depends on the answer.

Prints. Writes nothing, inside the repository or outside it. A collision has to
exist before the loader can be watched resolving one, creating a collision means
writing into somebody's `~/.claude/skills/`, and that is done by hand. The steps
are the last thing every run prints.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SKILL_FILE = "SKILL.md"

# The managed settings root per platform. The loader appends `.claude/skills`.
# Its own `--debug` line prints all three resolved roots, so a wrong guess here
# is visible the first time the by-hand steps below are run.
MANAGED_ROOTS = {
    "darwin": "/Library/Application Support/ClaudeCode",
    "win32": r"C:\Program Files\ClaudeCode",
}
MANAGED_ROOT_OTHER = "/etc/claude-code"

# The order the loader concatenates the roots in. `additional` is one
# `.claude/skills` per `--add-dir`, and `commands` is the deprecated
# `.claude/commands/*.md`, which arrive as skills with no directory of their own.
LOAD_ORDER = ("managed", "user", "project", "additional", "commands")


def managed_skills() -> Path:
    root = MANAGED_ROOTS.get(sys.platform, MANAGED_ROOT_OTHER)
    return Path(root) / ".claude" / "skills"


def user_skills() -> Path:
    """`CLAUDE_CONFIG_DIR` wins over `~/.claude`, and both end in `skills`."""
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    home = Path(configured) if configured else Path.home() / ".claude"
    return home / "skills"


def frontmatter_name(skill_md: Path) -> str | None:
    """The `name:` a SKILL.md declares, which overrides its directory name.

    A skill with no frontmatter name loads under its directory name, so a
    collision can be spelled either way and a listing keyed on directories alone
    misses half of them.
    """
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        if line.startswith("name:"):
            return line[len("name:") :].strip().strip("\"'") or None
    return None


def skills_in(root: Path) -> list[tuple[str, Path]]:
    """Every (loaded name, SKILL.md) under a skills root, sorted by name.

    A directory with no SKILL.md is skipped, which is what the loader does.
    """
    found = []
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return []
    for entry in entries:
        if not entry.is_dir():
            continue
        skill_md = entry / SKILL_FILE
        if not skill_md.is_file():
            continue
        found.append((frontmatter_name(skill_md) or entry.name, skill_md))
    return sorted(found)


def commands_in(root: Path) -> list[tuple[str, Path]]:
    """Every `.claude/commands/*.md`, under the name a session types."""
    try:
        return sorted((p.stem, p) for p in root.glob("*.md") if p.is_file())
    except OSError:
        return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe what Claude Code loads skills from.")
    ap.add_argument(
        "--project",
        default=str(Path(__file__).resolve().parent.parent),
        help="Project root holding .claude/. Default: the repository this probe sits in.",
    )
    args = ap.parse_args()

    project = Path(args.project).resolve()
    roots = {
        "managed": managed_skills(),
        "user": user_skills(),
        "project": project / ".claude" / "skills",
        "commands": project / ".claude" / "commands",
    }
    held = {
        name: (commands_in(path) if name == "commands" else skills_in(path))
        for name, path in roots.items()
    }

    print("Where the loader looks, in the order it concatenates the roots")
    for name in LOAD_ORDER:
        if name == "additional":
            print(f"  {name:<10}  one .claude/skills per --add-dir, between project and commands")
            continue
        path = roots[name]
        if not path.is_dir():
            state = "absent"
        else:
            state = f"{len(held[name])} skill(s)"
        print(f"  {name:<10}  {path}  {state}")

    print("\nWhat each root holds, under the name a session types")
    for name in LOAD_ORDER:
        if name == "additional" or not held.get(name):
            continue
        print(f"  {name:<10}  {' '.join(n for n, _ in held[name])}")
        for loaded, skill_md in held[name]:
            if name != "commands" and loaded != skill_md.parent.name:
                print(f"             {skill_md.parent.name}/ declares name: {loaded}")

    seen: dict[str, list[str]] = {}
    for name in LOAD_ORDER:
        for loaded, skill_md in held.get(name, []):
            seen.setdefault(loaded, []).append(f"{name} {skill_md}")
    collisions = {n: where for n, where in seen.items() if len(where) > 1}

    print("\nNames in more than one root")
    if not collisions:
        print("  none on this machine, so the loader resolves nothing here")
    for loaded, where in sorted(collisions.items()):
        print(f"  {loaded}")
        for line in where:
            print(f"    {line}")

    print(BY_HAND)
    return 0


BY_HAND = """
What this probe cannot see

A listing says which files exist. It does not say what the loader did with two
of one name: whether both entries survive into the session, and which one a
typed `/name` reaches. Watching that needs a collision, and a collision means
writing a SKILL.md into ~/.claude/skills/.

By hand, once, to settle it

1. Baseline. From the project root, with no collision in place:

       claude --debug-file /tmp/skills-before.log -p "reply with the single word ok"
       grep -E "Loading skills from|unique skills" /tmp/skills-before.log

   The second line reads: Loaded N unique skills (..., managed: a, user: b,
   project: c, additional: d, legacy commands: e). Keep N and b.

2. Create the collision, on a name this project ships:

       mkdir -p ~/.claude/skills/pick-work
       $EDITOR ~/.claude/skills/pick-work/SKILL.md

   Five lines, the first at column 0:

       ---
       name: pick-work
       description: Personal copy, for one measurement. Prints one marker.
       ---
       Reply with exactly MARKER-PERSONAL and stop.

3. On a scratch branch, replace the body of .claude/skills/pick-work/SKILL.md
   with: Reply with exactly MARKER-PROJECT and stop.

4. Count what loaded:

       claude --debug-file /tmp/skills-after.log -p "reply with the single word ok"
       grep -E "Loading skills from|unique skills|Skipping duplicate skill" /tmp/skills-after.log

   user: rises by one either way. The verdict is N. N+1 means both entries
   survived. N unchanged means one was dropped, and the "Skipping duplicate
   skill '<name>' from <source>" line names which.

5. Ask which one runs:

       claude -p "/pick-work"

   MARKER-PERSONAL: the personal copy is what a project's own name reaches.
   MARKER-PROJECT: the committed copy wins.
   Both: both load and both are reachable.

6. rm -rf ~/.claude/skills/pick-work, and drop the scratch branch.

Steps 1 and 4 write a log under /tmp, which is why they are here and not in the
probe. Put the two lines from step 4 and the marker from step 5 into issue #40
as a dated comment, then edit the body and the rule to match.
"""


if __name__ == "__main__":
    sys.exit(main())
