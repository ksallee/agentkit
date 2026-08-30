---
name: teardown
description: Take apart the shipped products that already solve a version of the decision in front of you, and record borrow or refuse per tool with the numbers read off the product rather than remembered. Use before drawing variants, when a moodboard needs what the screens do, and when a project's own reference list is empty.
---

# Tearing down a shipped tool

`design-process` step 1 checks a product shape against a teardown, and step 5
puts one on a moodboard with borrow or refuse per tool. This is how that gets
made.

**A teardown answers one decision.** "Study Linear" produces a gallery.
"Everyone here has a list of hundreds of rows and one action per row: what did
Linear, Raycast and Superhuman each do about selecting several of them" produces
a table somebody can build from. Name the decision first, and name it in the
project's nouns.

## What comes out

One table per decision, one row per tool.

| Column | What goes in it |
|---|---|
| Tool | The product, and the exact screen or state |
| What it does | The behaviour, in a sentence somebody could implement from |
| The numbers | Sizes, radii, durations, weights, counts, with where each was read |
| Borrow or refuse | One of the two, and why in a clause |
| Source | The URL, the screen, or the build and date it was measured in |

A refusal is worth as much as a borrow, and it is the half people leave out. A
tool that got the decision wrong tells the project what the cost of that
approach is, and the row stops the next session repeating the experiment.

## Preconditions

Check these and print the fix. Don't work around them.

| Needs | Check | Fix |
|---|---|---|
| A decision under study | ask | Stop. A teardown with no question is a screenshot collection |
| The running product, or what its makers published about it | open it | Where neither is reachable, the row says so and lends behaviour only |
| Somewhere for the output to land | `.agentkit/team.md`, `## Design`, `surface` | `design-process` step 8 has the three answers |

## Read the product, never your memory of it

Rule 9 is about a third party interface, and a shipped interface is one. What a
product did two versions ago is what an agent remembers about it, and a
teardown written from memory is a set of plausible numbers with a famous name
attached.

Where the numbers come from, in order of what they cost:

| Source | Gives | Costs |
|---|---|---|
| The maker's own writing: a changelog, a craft post, a design system page | numbers they chose to publish, and the reasoning behind them | Minutes. `design-references` says who publishes |
| The running product, inspected | computed styles, real sizes, the actual timing | An account and a session with it |
| A capture of one screen | reading order, density, what is on screen at once | Minutes |
| Somebody else's write-up | a claim to verify | Cheap and unverified. Cite it as that |

Take the exact value. `8px`, `160ms`, `cubic-bezier(0.32, 0.72, 0, 1)`, forty
rows on screen at 900px. "Tight spacing" is a description of a number that
somebody declined to read.

## Borrow or refuse, per row, with the tradeoff

The verdict goes on the row when the row is written, while the reason is still
in the session. A table of behaviours with no verdicts is one somebody has to
tear down a second time.

Three ways a row goes wrong:

- **Borrowing the look with none of the reasoning.** Take the radius, the
  duration and the type scale. Adopting a system whole is a decision about what
  the product is, and `design-references` says why.
- **A refusal with no cost named.** "Too heavy" is taste. "Its multi select
  needs a modifier key, so the one action people repeat forty times a day is
  two hands" is a finding.
- **Studying a competitor without saying so.** An artboard naming a product
  reads as an endorsement. Where the study is about what to refuse, the row
  says refuse.

## Where the output lands

| Output | Where | Why there |
|---|---|---|
| The table | The moodboard `design-process` step 5 builds | It is the input that step names |
| A decision the project takes from it | The design guide, as step 9 says | A decision in a transcript gets made again next month |
| A product worth reading again | The `## The project's own references` section of `design-references`, one line each | That section exists for the project's genre and starts empty |
| A number that governs motion | `motion`, where those numbers live | Step 9, and one home per fact |

**The shipped reference list in `design-references` stays hand written.** This
skill adds to the project's own section and rewrites nothing above it. A list
regenerated from a study has no source to check it against, and the people half
of that list is who to learn from over years rather than what one product does
this quarter.

## A teardown is dated evidence

It records what a product did on a day, and products ship. Nothing here is
maintained. When a decision comes back, run the study again and write a new
table with a new date beside the old one. A table edited in place to look
current is one whose numbers nobody can trace to a build.

## Excuses

| Excuse | Reality |
|---|---|
| "I know what Linear does." | You know what it did in some version. The numbers on the row have to come from somewhere citable. |
| "I tore down five tools, so the coverage is good." | Coverage was never the goal. `design-process` step 4 says how many references a variant set needs, and one decision studied properly beats five galleries. |
| "The numbers were not published, so I estimated." | Then the row lends behaviour and carries no numbers, and it says so. An estimate with a product name on it reads as measured. |
| "It looks better, so borrow." | Name what it costs the person using it. A verdict with no cost is taste with a citation. |
| "I put it in the reference list so it stays current." | Nothing here is maintained. The list holds who to read; the table holds what one product did on one date. |
