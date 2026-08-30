# agentkit

How two people and their agents build a project together: the rules, the
skills, the role guides and the design pipeline, extracted from a project that
grew them and proved them on real work.

Private. Built for the way we work rather than for adoption by strangers.

## What it gives a project

- **A way of working that survives being forgotten.** The issue body is the
  record. A claim carries a measurement. A stated preference is written into
  the file that reads it next.
- **Gates that check what a rule states**, so a rule with a mechanical
  consumer does not decay into a convention nobody follows.
- **Three layers.** What the template ships, what the project decides, and what
  one person prefers, with a stated precedence between them.
- **A front half.** Shaping a topic into an issue worth starting, research that
  answers pre-drafted questions, and decisions that record what would reopen
  them.

## Adopting it

```sh
git clone git@github.com:ksallee/agentkit.git
python3 agentkit/bin/adopt /path/to/your/project              # the plan
python3 agentkit/bin/adopt /path/to/your/project --write --pack python
```

The plan is the default and writes nothing, because the target is your
repository. A write seeds every file in `seeds.json`, records a sha256 for each
in `.agentkit/manifest.json`, and seeds `.agentkit/gates.toml`, `team.md` and
`phase.json` once. Rerun it to update: a file you have not touched is rewritten,
a file you have edited is replaced and yours is kept beside it as `.local`, with
both names on the line.

A write also renders your `CLAUDE.md` from the answers you gave: the layers, the
role guides, the rules that travel, and your own 1 to 8 held open. A project
that already has a router keeps it untouched, and the `adopt` skill asks how you
want the two reconciled.

Your `.gitignore` gets a delimited block carrying `.agentkit/local.*`,
`.claude/worktrees/` and the two artboard patterns a `design/` run writes, and
it is the one file a rerun edits in place. Git reads
every line of it on its own, so the block is rewritten and every line outside it
stays where you put it.

The `adopt` skill asks the six answers the team layer and the router need. The
pack is the one it refuses to guess, because a gate list naming a command you do
not run makes rule 17 disagree with CI.

## What it is not

No plugin and no marketplace. A committed `.claude/skills/` entry loads with no
install step, which is the property a plugin was chosen for and does not have,
measured 2026-08-29. No dependency on another skill collection, because a
template whose claim is that a decision returns the same answer next quarter
cannot rest on something that moves under it.

## Where it came from

`ksallee/mac-hours`, issue 172, which carries every decision and the
measurement behind each one.
