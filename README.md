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
python3 agentkit/bin/adopt /path/to/your/project
```

`adopt` asks what the project is, writes the committed half, and records a
sha256 per seeded file in `.agentkit/manifest.json`. Rerun it to update: a file
you have not touched is rewritten, a file you have edited is kept and reported.

## What it is not

No plugin and no marketplace. A committed `.claude/skills/` entry loads with no
install step, which is the property a plugin was chosen for and does not have,
measured 2026-08-29. No dependency on another skill collection, because a
template whose claim is that a decision returns the same answer next quarter
cannot rest on something that moves under it.

## Where it came from

`ksallee/mac-hours`, issue 172, which carries every decision and the
measurement behind each one.
