# agentkit

The scaffolding a project adopts: the rules, the skills, the role guides and
the design pipeline.

---

# Rules: these are not optional

**Every task, every session, human or AI.** The reasoning is in
[`docs/development/WORKFLOW.md`](docs/development/WORKFLOW.md).

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
absence means nobody has been asked yet. Where that file belongs for a project
with no data directory is #15; this path is what works today.

## 1 to 8 are reserved for the project

These are the constraints a project locks before writing code: its storage
model, its precedence, what it refuses to build. Only that project has the
answers, and `shape` asks for them first. The numbers stay open so a project's
rules and these never collide in a citation.

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
how a project gets everything else here.

Two skills have a slash command, because a command is the one thing a
`description` cannot advertise. **`pick-work`**, as `/work`, says what to do
next. **`wrap-up`**, as `/done`, ends a session: the tree is clean, the prose
gets read against STYLE.md, and every preference the session stated is written
into the file that reads it next.

The rest are named nowhere. Every `SKILL.md` opens with a `description` written
to be read at load time, so a list here would be that description again, in a
file with no way to know a skill arrived. It drifted twice in two days, at #31
and #34, which is what a second copy does. `tests/test_skills.py` asserts the
two that stay: a command names a skill that exists, and a skill named here
exists.

The team layer is data that skills read. Skill precedence doesn't exist: two
skills of one name both load.
