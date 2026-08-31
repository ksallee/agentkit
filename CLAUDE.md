# agentkit

The scaffolding a project adopts: the rules, the skills, the role guides and
the design pipeline.

---

# Rules: every task, every session, human or AI

Breaking one costs two different things. Rules 11, 12, 13, 15, 16, 17, 19 and
24 fail a check: `bin/verify` over `.agentkit/gates.toml`, `bin/check-style`,
and `bin/check-process` over the pull request, its labels and its commits.
Rules 0, 9, 10, 14, 18 and 20 to 23 reach a reader and nothing else, so
skipping one stays invisible until somebody needs what it would have left
behind: the issue that predates the branch, the preference written into the
file that reads it next, the pull request body that says what was verified.

Nothing here compels an agent, and a session that skipped either kind has not
done the work. [`docs/development/WORKFLOW.md`](docs/development/WORKFLOW.md)
names which check reads which rule, and carries the reasoning behind each.

## 0. Read the layers, in order, and let the right one win

Three layers. Precedence is per field.

| Layer | Where | Wins on |
|---|---|---|
| Shipped | this repository, seeded by `adopt` | nothing; it is the default |
| Team | `.agentkit/` in the project, committed | anything two people must agree on |
| Personal | `.agentkit/local.md`, gitignored | taste |

**Team wins on the gate list and the phase.** One person opting out of the
test suite isn't a preference. **Personal wins on taste**: how work is
delivered, which guide is read, how large a pull request should be.

`.agentkit/team.md` holds conventions and who owns what. `.agentkit/gates.toml`
declares the gates; `bin/verify` runs them. `.agentkit/phase.json` says
`shaping` or `building`. `.agentkit/local.md` is one person's file, and its
absence means nobody has been asked yet.

## 1 to 8 are reserved for the project

These are the constraints a project locks before writing code: its storage
model, its precedence, what it refuses to build. Only that project has the
answers, and `shape` asks for them first. The numbers stay open, so a citation
of rule 3 means the project's rule 3 in every project that adopts this.

An empty section invites invented constraints, so it stays absent until
something is settled.

## 9. Probe an external interface, never assume it

Before writing code against any third party library, API or tool, put a small
script in `probes/` that calls the real thing and prints what came back. Commit
it. Payload shapes and field names vary by version, and an assumption baked
into a parser fails quietly on the one machine that matters. A reader reruns a
probe instead of trusting a docstring.

Probes print. They never write to a database. Standard library only, so a probe
runs before the project installs.

**This rule only applies where the project touches something it doesn't
control.** With no external interface, drop it. A dead rule teaches that rules
are decorative.

## 20. Do not widen scope silently

Fold in a bug you hit while working: file it, close it in the same pull
request, say so in the body. The thing to avoid is an unrelated change nobody
can find later. The test: would a reader of the pull request expect it?

## 24. Follow STYLE.md in everything you write

[`docs/development/STYLE.md`](docs/development/STYLE.md) governs markdown,
comments, docstrings, commit messages, issue and pull request bodies. No em
dashes, no "not X, Y", no hedging preambles, no marketing vocabulary.
`bin/check-style` gates the mechanical half, here or in any project it's
given. Voice, restatement and padding are a reading, and `wrap-up` does it.

## The rest load when they apply

Rules 10 to 19 and 21 to 23 are in
[`docs/development/WORKFLOW.md`](docs/development/WORKFLOW.md): how work is
filed, branched, committed, reviewed and merged. They apply when somebody
opens or files work, not every turn. #10 is the job that checks the half a
machine can.

A rule keeps its number wherever it lives, so a citation survives a move.

---

## Task knowledge lives in skills

Loaded on demand from `.claude/skills/`, committed, available the moment
somebody clones. No plugin, no install step.

**`adopt`** seeds this scaffolding into a project and updates it later. It is
how a project gets everything else here, and it stays here. Every adoption runs
from an agentkit checkout, so `seeds.json` withholds the skill and its command
from the projects it seeds, the way it withholds `bin/adopt`.

Three skills have a slash command, because a command is the one thing a
`description` cannot advertise. **`adopt`**, as `/agentkit`, sets a project up
or updates one, and reads the rest of the line as free text it says back before
writing anything. **That command is how an adoption starts here.** `bin/adopt`
is the tool under it, and reaching for the tool first skips the say-back, the
answers and the plan, which are the parts that stop a write going into the
wrong directory. **`pick-work`**, as `/work`, says what to do next.
**`wrap-up`**, as `/done`, ends a session: the tree is clean, the prose gets
read against STYLE.md, and every preference the session stated is written into
the file that reads it next.

The rest are named nowhere. Every `SKILL.md` opens with a `description` written
to be read at load time, so a list here would be that description again, in a
file with no way to know a skill arrived. It drifted twice in two days, at #31
and #34. `tests/test_skills.py` holds three couplings: this file and the skills
it names, `bin/adopt`'s outcomes and the table in the `adopt` skill, and a
description's step count and the body under it. It also asserts this file lists
no skill it need not, so the removal cannot quietly come back.

Skills read the team layer as data, so it wins on a convention. A skill name
has no such protection. Two skills of one name both load, and a typed name
reaches the personal copy, so a project's committed skill loses to one its
reader already had. `probes/skill_precedence.py` prints the roots in the order
they concatenate (#40).
