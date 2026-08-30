---
name: pick-work
description: Summarise the open issues and help choose what to do next, grouped by what each one needs in order to be verified. Use when someone asks what to work on, says they have no particular task, or wants to know what is pending.
---

# Picking work

Offer this only when the operator has no task in mind. Someone who arrived with
one gets that instead.

## 1. Read the board

```sh
gh pr list --state open --json number,title,statusCheckRollup
gh label list --json name,description
gh issue list --state open --limit 30 \
  --json number,title,body,labels,assignees,updatedAt
```

**Open pull requests first.** A finished change waiting on review outranks a
new one started, and it is the thing most easily forgotten.

**Read every body in full.** Rule 23 puts what is settled, what is open and
what was ruled out in the body. Titles and labels carry none of it.

**Read the label descriptions.** They are how this skill learns a project's
taxonomy without holding a copy. Whoever made the label wrote the definition;
use it.

**Skip the comments.** A comment holding a decision the body lacks is a process
failure to fix in the body. Reading every thread on every invocation costs more
than it catches. The exception is one issue about to be started, where
`gh issue view <n> --comments` is worth it once for the measurements and the
reversals rule 23 keeps there on purpose.

**Check `.agentkit/phase.json`.** While it says `shaping`, say so: an empty
board is not a backlog.

## 2. Group by what it takes to verify

Never by size. "Medium" tells nobody anything.

Use the project's `effort:` labels and their descriptions. Those definitions
differ per project on purpose, so do not import one from elsewhere. An issue
with no `effort:` label gets placed by hand, and say that you placed it.

## 3. Parallelism

**An `area:` label is not a safety key.** Two issues in different areas still
edit the same files, and two branches that each pass their gates conflict on
merge.

Derive the ceiling from the board: count the `area:` labels, run at most one
issue per area, and list the files each will touch before proposing a set. When
the sets overlap, sequence them and say why. Anything changing a shared
mechanism runs alone, because what everything else is verified against moves
underneath it.

A board with no `area:` labels gets none of this. Say it has no taxonomy to
reason from.

## 4. Propose, then wait

Three or four issues, never the whole backlog. Each gets a number, one line on
why now, what it touches, and how it would be verified.

**Nothing starts without an explicit yes, and no agent is spawned without one.**
Parallel agents cost tokens and merge time. The operator decides.

## 5. Then the normal process

Rules 10 to 18 in `docs/development/WORKFLOW.md`: file it, assign it, branch off
`main` named for the number, `bin/verify` green, and a pull request opening
`Closes #N` that says what was verified and what was not. Merging is settled
per project.

## Known limit

`--limit 30 --json body` fetches every body in one call. Correct at twenty
issues, and it fills a context window at two hundred. Say so when the board is
large enough to matter.

| Excuse | Reality |
|---|---|
| "The titles are enough to propose from." | Rule 23 puts what is settled in the body. |
| "I will read the comments to be safe." | Sixteen threads an invocation, for a failure that belongs fixed in the body. |
| "These three are different areas, so they parallelise." | Different areas edit the same files. List them. |
| "I will start the obvious one while they decide." | Nothing starts without a yes. |
