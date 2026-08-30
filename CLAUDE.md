# agentkit

The scaffolding a project adopts: the rules, the skills, the role guides and
the design pipeline. Extracted from `ksallee/mac-hours`, where every rule below
was used on real work before it was written down here.

---

# Rules: these are not optional

**Every task, every session, human or AI.** The reasoning is in
[`docs/development/WORKFLOW.md`](docs/development/WORKFLOW.md).

## 0. Read the layers, in order, and let the right one win

Three layers, and the precedence between them is per field rather than
uniform.

| Layer | Where | Wins on |
|---|---|---|
| Shipped | this repository, seeded by `adopt` | nothing; it is the default |
| Team | `.agentkit/` in the project, committed | anything two people must agree on |
| Personal | `context.md` beside the project's data, never committed | taste |

**Team wins on the gate list and the phase.** One person opting out of the test
suite is not a preference. **Personal wins on taste**: how work is delivered,
which guide is read, how large a pull request should be.

`.agentkit/team.md` states the project's conventions and who owns what.
`.agentkit/gates.toml` declares the gate commands and `bin/verify` runs them.
`.agentkit/phase.json` says `shaping` or `building`. `context.md` is one
person's own file, and its absence means nobody has been asked yet.

## 1 to 8 are reserved for the project

These numbers belong to the constraints a project locks before it writes code:
its storage model, its precedence, what it refuses to build. They are the
answers only that project has, and they are the first thing `shape` asks for.
The numbers are held open so a project's own rules and this scaffolding's rules
never collide in a citation.

A project with none of them yet has none of them. An empty section invites
invented constraints, so it stays absent until something is actually settled.

## 9. Probe an external interface, never assume it

Before writing code against any third party library, API or tool, put a small
script in `probes/` that calls the real thing and prints what came back. Commit
it. Payload shapes and field names vary by version, and an assumption baked
into a parser fails quietly on the one machine that matters. A probe is
reproducible, a reader reruns it instead of trusting a docstring, and it costs
less than the debugging session it replaces.

Probes print. They never write to a database. Standard library only, so a probe
runs before the project installs.

**This rule earns its place only where the project touches something it does
not control.** A project with no external interface gets an empty `probes/` and
should drop the rule rather than keep a dead one.

## 20. Do not widen scope silently

Folding in a bug you hit while working is fine and often better than a second
branch: file it, close it in the same pull request, and say so in the body.
What is not fine is an unrelated change nobody can find later. The test: would
a reader of the pull request expect it?

## 24. Follow STYLE.md in everything you write

[`docs/development/STYLE.md`](docs/development/STYLE.md) governs markdown,
comments, docstrings, commit messages, issue and pull request bodies. No em
dashes, no "not X, Y", no hedging preambles, no marketing vocabulary.
`bin/check-style` gates the mechanical half, over this repository and over any
project it is given.

## The rest load when they apply

Rules 10 to 19 and 21 to 23 are in
[`docs/development/WORKFLOW.md`](docs/development/WORKFLOW.md): how work is
filed, branched, committed, reviewed and merged. They apply when somebody is
opening or filing work rather than on every turn, and
`.github/workflows/process.yml` checks the half of them a machine can check.

Numbers are stable. A rule keeps its number wherever it lives, because a
citation that survives a move is the point.

---

## The layers, and what breaks without them

A project read by two people needs somewhere to put a decision that is neither
shipped nor personal. Skill precedence cannot serve that: the loader
deduplicates by resolved file path and never by name, so a personal skill and a
project skill of the same name both load and neither shadows the other,
measured 2026-08-29. The team layer is therefore data that skills read, which
is the shape `context.md` already had.

## Task knowledge lives in skills

Loaded on demand from `.claude/skills/`, committed, and available the moment
somebody clones. There is no plugin and no install step.

**`adopt`** seeds this scaffolding into a project and updates it later. It is
the only skill here.

The front half, the loop and the design skills are settled and not built.
#10, #11 and #12 carry them. Nothing is named here until it exists, so a
reader who goes looking finds what the router says they will.
