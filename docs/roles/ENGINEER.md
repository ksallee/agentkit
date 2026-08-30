# Engineer's guide

Owns the data model, the pipeline that fills it, and every number a screen
shows. Read `CLAUDE.md` first: rules 1 to 8 are whatever this project locked
before it wrote code, and this guide assumes them.

## The one number, computed once

Every figure a person reads comes from one place. When a component adds two
durations, sums a column or rounds a total, that is a second implementation of
the thing that produced them, and the two disagree in the week that matters.
Return the number the screen needs, and say no to a design that derives one.

The same holds for a report, an export and a test fixture. Three code paths
that each compute a total will each be right on the day they were written.

## The storage model is the expensive decision

Storage is the one thing a project cannot walk back cheaply. Adding a table
needs an issue saying why the existing ones are wrong, because a schema grows
by one table at a time and nobody notices until a query has to join five.

Write the invariants down where the code enforces them, as properties rather
than as history:

- Ordering and comparison. "Every timestamp is UTC and sorts
  lexicographically, so a range query can use string comparison."
- Units and scales. "`duration_s` is seconds, always float."
- What is derived and what is stored. A stored value that could have been
  derived is a value that can go stale, and it needs a reason.
- Non-local coupling. "The rule engine and the editor's schema accept the same
  op set."

## A pipeline runs in stages, and each stage is rerunnable

Split the work so that any stage can be rerun over its inputs and produce what
it produced before. Ingest, then derive, then aggregate. A stage that mutates
its own input cannot be rerun, so a bug in stage three costs a reimport.

Determinism is the property that makes a bug findable. Given the same inputs,
the same output, every time. Where randomness or a clock is genuinely needed,
it is an input to the stage and not a call inside it.

## Where a model is allowed

A model may cluster, order, group or draft. A model may not decide a value that
a person will read as fact, and it may not sit inside a recompute where nobody
sees it run. The test: could you explain to somebody why their number came out
that way, from the code, a year later? A ranked guess in the middle of a
pipeline fails that test, and it fails it silently.

Drafting is where models pay: a proposed rule somebody accepts on screen, a
suggested grouping, a first pass at a name. The person is the one who commits
it.

## Probe before you write against anything external

Rule 9. A third party library, an API, a CLI, a file format somebody else
writes: put a script in `probes/` that calls the real thing and prints the
payload, and commit it. Field names and shapes vary by version, and an
assumption baked into a parser fails on one machine and nowhere else.

Probes print, they never write, and they use the standard library only, so one
runs before the project installs.

## The gates are the contract

Rule 17. What runs is declared in `.agentkit/gates.toml` and nowhere else, and
`bin/verify` runs it. Adding a check means adding a gate, so CI and a local run
cannot disagree.

A test that cannot fail is not a test. A gate asserting that a function returns
something is worth less than one asserting the invariant it exists to hold. The
tests worth writing are the ones a future refactor would break.

## Handing work back

When a design asks for a number the pipeline does not produce, file it as an
issue against this guide. When a design asks for a number that would be
wrong, say which invariant it breaks. Neither one gets solved in a component.

`.agentkit/team.md` says who wins when two roles disagree.
