---
name: pick-work
description: Summarise the open issues and help choose what to do next, grouped by what each one needs in order to be verified. Use when someone asks what to work on, says they have no particular task, or wants to know what is pending.
---

# Picking work

## When to offer this

Only when the operator has no task in mind. If they arrived with one, do that
instead. A backlog review nobody asked for is an interruption, and offering it
every session turns a good prompt into noise.

## 1. Read the board

```sh
gh pr list --state open --json number,title,statusCheckRollup
gh label list --json name,description
gh issue list --state open --limit 30 \
  --json number,title,body,labels,assignees,updatedAt
```

**Report open pull requests first.** A finished change waiting on review is
worth more than a new one started, and it is the thing most easily forgotten.

**Read the bodies, and read them in full.** Titles and labels do not say what
an issue needs settled, so a proposal built on them is a guess.

**Read the labels too, and their descriptions.** They are how this skill learns
one project's taxonomy without carrying a copy of it. A label's description is
written by whoever made the label and is the definition to use.

**Do not read comments.** Rule 23 makes the body the record: what is settled,
what is still open and what was ruled out all live there. A comment carrying a
decision the body does not is a process failure to fix in the body rather than
to work around here. Reading every comment thread on every invocation costs
more than it catches, and it makes the convention optional the moment it is
relied on.

The exception is one issue the operator is about to start. Then
`gh issue view <n> --comments` is worth it once, for the measurements and the
reversals that rule 23 keeps in comments on purpose.

**Check the phase.** `.agentkit/phase.json` says `shaping` or `building`. While
it says `shaping`, an empty board is not a backlog and the useful offer is to
shape something rather than to pick from three issues. Say which phase the
project is in when it is `shaping`.

## 2. Group by what each needs to be verified

Group by verification, never by size. "Medium" tells nobody anything. What it
takes to know the change worked decides whether it can be handed off.

Use the project's own `effort:` labels and the descriptions attached to them.
Those descriptions are the definitions, and they differ per project on purpose:
one project's `quick` is fixtures alone, another's is a service that has to be
running. Do not restate a definition from another project here.

An issue with no `effort:` label gets read and placed by hand, and say that you
did.

## 3. Parallelism: the constraint that actually bites

**An `area:` label is not a safety key.** Two issues in different areas can
still edit the same file, and two branches that each pass their own gates
conflict on merge.

Derive the cap from what the board actually has rather than from a number
written here:

- Count the `area:` labels. That is roughly the ceiling on useful parallel
  work, and it is a ceiling rather than a target.
- **At most one issue per `area:` in flight.**
- Before proposing a parallel set, list the files each will touch and check the
  sets are disjoint. When they overlap, sequence them and say why.
- **Anything changing a shared mechanism runs alone**, because the thing every
  other issue is verified against moves underneath them.

A project with no `area:` labels gets none of this advice. Say that the board
has no taxonomy to reason from rather than inventing one.

## 4. Propose, then wait

Offer three or four issues, not the whole backlog. For each give the number,
one line on why it is worth doing now, what it will touch, and how it would be
verified.

**Never start work, and never spawn agents, without an explicit yes.** Parallel
agents are a real cost and a real merge burden. The operator decides whether to
spend it.

## 5. Then follow the normal process

Rules 10 to 18 in `docs/development/WORKFLOW.md`: file the issue, assign it to
yourself, branch off `main` named after the issue number, get the gates in rule
17 green with `bin/verify`, and open a pull request whose body starts with
`Closes #N` and says what was verified and what was not. **Do not merge it**
unless the project has said you may.

## Known limit

`gh issue list --limit 30 --json body` fetches every body in one call. That is
deliberate and correct at twenty issues and it fills a context window at two
hundred. Say so when a board is large enough for it to matter, rather than
proposing from a truncated read without mentioning it.

| Excuse | Reality |
|---|---|
| "The titles are enough to propose from." | Rule 23 puts what is settled in the body. A proposal from titles is a guess wearing a number. |
| "I will read the comments to be safe." | Sixteen threads per invocation, to catch a process failure that belongs fixed in the body. |
| "These three are all different areas, so they are parallel." | Different areas edit the same files. List them and check. |
| "I will start the obvious one while they decide." | Nothing starts without a yes. |
