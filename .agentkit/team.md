# agentkit

The scaffolding a project adopts: the rules, the skills, the role guides and
the design pipeline.

## The layer this file is

Committed, and it wins over anybody's `.agentkit/local.md` on anything two
people have to agree on. One person opting out of the gate list is a decision
two people make.

## Who reviews and who merges

The agent merges the pull requests it opens. Two conditions come with that:

- **The gates pass first.** `bin/verify` prints a table, and that table goes in
  the pull request body. Rule 17: a gate reported green without its output in
  the session did not pass.
- **The operator QAs after the fact.** A defect found then is a new issue, and
  the branch that would have waited for a review is already off the board.

**A second reader reopens it. It was reopened and it held.** @salleedesign got
write access on 2026-08-30 and the line was asked the same hour. He adopts this
scaffolding into his own projects and does not work on it, so agentkit has one
operator and the clause describes a situation that has not arrived. It gets
asked again at his first review of a pull request here.

**While this is a prototype, that covers everything.** Asked on 2026-08-30
after a session held two pull requests back for review, on the grounds that
they carried agentkit's first hard external dependency and a new seeded
directory: "you can merge everything when done, run done, i'll qa everything on
main tomorrow. This is a prototype still anyway." So size is not a reason to
wait, and neither is a new dependency. The gates and the QA are the whole
condition.

Settled 2026-08-29 in #6, which carries what the alternative was.

## Who owns what

One row per area, naming who decides when two answers conflict. The areas are
the `area:` labels on the board.

| Area | Owner |
|---|---|
| Rules: `CLAUDE.md`, `WORKFLOW.md`, `STYLE.md` | @ksallee |
| Mechanism: `bin/`, `seeds.json`, the manifest | @ksallee |
| Skills: what a project gets under `.claude/` | @ksallee |

One person owns every area, so no row settles a disagreement today. A second
owner is one edit to the table, made when somebody takes an area rather than
when they arrive.

**@salleedesign adopts this, he does not maintain it.** Write access, no area,
and the first person to run `bin/adopt` against a project whose rules nobody
here wrote. That makes him the audience for `templates/`, the role guides and
everything under `.claude/skills/`, and the reason a question about what a
seeded project gets outranks a question about what this repository has. #25 is
where that run is tracked, and it stopped being hypothetical on 2026-08-30.

## Conventions this project settled

**Commit trailers: rule 13's shipped default, unchanged.** The rule states the
two lines and this layer overrides nothing about them.

**CI runs on this project's own self-hosted runner, label `agentkit-local`.**
Settled in #194 and dogfooded here first. Both workflow files name it in their
`runs-on` lines, so no hosted minutes are billed and the gates run only while
that machine is up. The machine is a UTM VM named "Github Runners" on the
operator's Mac, reachable at `ssh -p 2222 gh-runners@127.0.0.1`, with one
runner service per adopted repository. `sources.yml` stays hosted: it runs
weekly whether or not that Mac is awake.

A dead runner fails silently: a queued job waits for a machine that will
never claim it, and the pull request reads as slow CI. Before opening a pull
request, check `gh api repos/ksallee/agentkit/actions/runners` reports the
runner online. A check still queued two minutes after a push means the runner
is down: say so and name the VM instead of waiting. The preflight job in
`gates.yml` runs the same check on every opened pull request.

Moving back to hosted CI is a hand edit, and this is the whole of it:
`ubuntu-latest` in both files' `runs-on` lines, the preflight job in
`gates.yml` deleted, and this section with it.

## Design

Two settings the design skills read. Rule 0 puts them here because two people
open the same deliverable. `references` was a third until #123 removed it.

| Setting | Values | Meaning |
|---|---|---|
| surface | canvas, file, none | where a finished design lands |
| review | artifact, paper, none | which medium in-progress design reaches a reader through |

**agentkit: surface `none`.** This repository ships
scaffolding and draws no screens, so `design-process` step 8 has nothing to
publish and steps 1 to 7 apply to whatever a project draws with them. #25 is
where the skills get exercised in a project that has screens.

`canvas` publishes the artboards with click-to-edit and PNG or PDF export,
which needs a paid plan and stores the content on somebody else's
infrastructure. `file` keeps them at a path in the repository, named after the
value: `file, design/`. `none` publishes nothing. `design-references` holds
the reference list itself and reaches no service, so there is no second row to
answer. #123 removed one, and #131 would put it back.

**agentkit: review `artifact`.** In-progress design reaches a reader as a
published Claude artifact, republished in place each pass so one link stays
current. `paper` is the second medium, for a designer who already pays for
Paper Desktop, and nothing writes to it until a probe prints what its local
MCP server returns (#195). `none` shows nothing before step 8. The row is
`artifact` here for the same reason `surface` is `none`: this repository draws
no screens, and the value is what an adopted project inherits.

One designer's own preference goes in `.agentkit/local.md` instead. Two
designers on one project can want different media, and this row says what the
project does rather than what either of them prefers.

A skill reads this section as prose. No machine does, and no gate could: the
one consumer is a person or an agent halfway through a design task, there is
nothing about a pull request that a wrong answer here would break, and a
checker cannot tell a project that chose `none` from one nobody asked. A
project whose team file has no `## Design` section has been asked nothing, and
the skill says so instead of picking a value.
