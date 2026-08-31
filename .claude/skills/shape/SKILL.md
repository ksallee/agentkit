---
name: shape
description: Ask a project for the constraints it locks before writing code, file the questions as an issue carrying what each costs to answer, and write the settled answers into the rules its router holds open. Use after `adopt` has run, when somebody says "shape this project" or "what are our rules", and when a constraint gets reversed and the record has to say so.
---

# Shaping a project

Two files come out of a shaping pass, and they hold different halves.

| File | Holds | Read by |
|---|---|---|
| The shaping issue | every question, who can answer it, what answering costs, what got settled and what reversed it | somebody deciding whether to start the work |
| `CLAUDE.md`, the project's own rules | the settled constraint, one paragraph each, no history | every agent, every turn |

**Only the operator answers.** A constraint is a decision somebody makes, and a
codebase is what got built before it. Reading the source and writing
an answer produces a rule nobody agreed to, which every session after it treats
as settled. Ask, take "we have not decided" as an answer, and file it as open.

## Preconditions

Check these and print the fix. Don't work around them.

| Needs | Check | Fix |
|---|---|---|
| Somebody in the session who can answer | ask | Stop. Nothing here is answerable from the tree |
| A router with the numbers held open | `grep -n "^## 1 to 8" CLAUDE.md` | `adopt` seeds it. On a router the project wrote, ask where its constraints already live |
| Somewhere to file the questions | `gh issue list` | Without a tracker the answers still reach the router. Say that the reasoning has nowhere durable to go, and offer a file under `docs/` |
| The session is in the project, not in the agentkit checkout | `git remote -v` | `cd` there first. `gh` reads the working directory's remote, so a run from the wrong one files the project's constraints against the template |
| The process rules, in the session before the first word of output | `ls docs/development/WORKFLOW.md docs/development/STYLE.md` | Read both now. Where the project keeps its process rules elsewhere, read that file instead |

**Read those two before anything else here runs.** Everything this skill
produces is written by hand: an issue body under rule 22, rules under rule 23, a
branch under rule 11, a pull request under rule 16, and every word of the four
under rule 24. `adopt` needs no such row, because `bin/adopt` renders its files
and owns the process around them.

## Read the project before asking it anything

`.agentkit/team.md` carries the name, the summary, who merges and the design
settings. `.agentkit/phase.json` says `shaping` or `building`. The README and
the tree say what exists. Read all of it, then say back what is already
answered.

A skill that asks a question the team layer answers teaches the operator that
the questions are a form to fill in. It also burns the one pass where their
attention is on constraints.

## The questions, in this order

Six openers, in one pass. Each answer narrows the one below it, so keep the
order of the table.

| Ask | What it settles | What answering costs |
|---|---|---|
| What will this refuse to do, however often it is asked for? | the scope, and the work that never gets started | A conversation. The cheapest of the six, and it deletes work |
| What does it store, and which of that is the truth? | the storage model: what is source, what is derived, what can be recomputed | A conversation, unless the shape of the data is unknown. Then a probe, per rule 9 |
| When two of those disagree, which one wins? | precedence | A conversation. Expensive to reverse once code reads both |
| What must never happen here, even once? | the failure this project would not survive: a leak, a wrong number shown as a fact, a lost store | A conversation. It also says what rule 19 covers in this project |
| Who acts on it, and what do they act on? | the unit a screen gets built around | A conversation, and `design-process` step 1 needs the answer before anything is drawn |
| What does it depend on that it does not control? | which external interfaces exist, and whether rule 9 stays alive here | A probe per interface, so hours rather than minutes |

**Rewrite each one in the project's own nouns before asking it.** "What does
this refuse to build" gets a shrug. "Does this ever show an hour it did not
measure" gets an answer, and the answer is a rule.

**Ask with `AskUserQuestion`, four questions and then two.** The tool takes four
per call. Nothing in the six is derivable from the tree, so none of them can be
dropped to make six fit one call, and the split follows the dependency the order
already carries: the first four, then the last two written from what the first
four answered. A run on 2026-08-30 opened with all six in prose in one message,
and the operator stopped it and asked for the question tool.

**Every option carries a `preview` holding a real file tree, a real path or real
code.** That is what the answer rate turned on in the same run: 2 useful answers
out of 4 in the prose pass, 12 out of 12 after the switch. Two of those first
four option sets had no correct answer in them, and the operator spent the reply
correcting the frame. Three adjectives are three plausible things somebody has
to hold in their head at once. An option whose preview shows
`experiments/<feature>/index.html` beside `reference.html` gets taken or
rejected in seconds.

**One option in every list is "we have not decided".** The opening of this skill
takes that as an answer, and a question offering it gets it. In the same run
"write no rule for this" was on the list for what makes a candidate boring, the
operator took it, and the question stayed open with their name on it.

Six openers, and a project's list runs longer. Anything the operator raises
joins the issue. The numbering below is capped and the question list is not, so
an open question with no rule behind it is a normal state.

## What earns a number

Three tests, and a candidate passes all three.

- **A session on day 30 would act differently.** Otherwise it is background.
- **It can be broken.** Name what breaking it costs. A constraint with no
  failure attached is a slogan.
- **It is the project's, and no other layer already holds it.**

Rule 0 says where the rest goes. How work is delivered to one person goes in
`.agentkit/local.md` under rule 21. A convention two people share goes in
`.agentkit/team.md`. A fact a machine can check goes in a gate in
`.agentkit/gates.toml`, never in prose.

## Numbering, and what a number promises

A number, once written, points at one constraint for the life of the project.

- **Assign the lowest number this project has never used.** Settle three
  constraints and they are 1, 2 and 3.
- **Within one pass, number them in the order the questions were asked.** Four
  answers arrive at once, and the table above breaks the tie, so two
  people running the same pass reach the same numbers.
- **A reversed constraint keeps its number.** The text is rewritten in place. A
  citation in a commit message from month one still lands on the rule it meant,
  and the issue says what changed.
- **A dropped constraint retires its number.** Nothing is renumbered, and the
  number is never handed to a different rule.
- **Eight is the budget.** A project that spends all eight and needs a ninth has
  more constraints than the numbering holds. Say so in the issue instead of
  taking a number from the shipped set.

Never write 9, 20 or 24, and never write anything in the range 10 to 23. Those
are the shipped rules, they keep their numbers in every project, and a
collision makes every citation ambiguous.

## The issue

Rule 22 is the shape: the questions lead, ahead of any proposal, and each one
carries what it would cost to answer and who can answer it. Title the outcome.
File it with `--body-file` under rule 14, after reading `gh label list` under
rule 15.

One section per question, in the order above, each carrying:

- the question in the project's words
- who can answer it
- what answering costs
- its status: open, settled with the number it took, or reversed

Rule 23 governs it from then on. The body is edited in place, so a settled
question stops being listed as open. A measurement, a probe result or a
reversal goes in a comment as dated evidence, and the body changes to match.

## The section in the router

The project's rules are everything between the end of rule 0 and the `## 9.`
heading. On a first pass that span is the `## 1 to 8 are yours` note `adopt`
seeded. On every pass after it, the span is the rules themselves plus the
closing block, and the note is gone. Find it by its end, replace it whole, and
touch nothing else in the file.

```markdown
## 1. The constraint, stated as what holds

What it requires or forbids, in two or three sentences, and what breaks when
somebody breaks it. No history: the issue carries why.

## 2. The next one

...

## 1 to 8, and where the reasoning is

Open: 3 to 8. <the shaping issue, or the file standing in for it> carries every
question, what each costs to answer, and what reversed the ones that changed.
It is edited in place.
```

Three things that form protects.

**The rules read as `## N.`, exactly like the shipped ones**, because a reader
citing "rule 2" and a reader citing "rule 20" are doing the same thing.

**The closing block explains the gap.** A router running 0, 1, 2, 9 reads as a
set somebody deleted from. Naming the open numbers says they are held rather
than lost. When all eight are spent, the block keeps its heading and its first
line reads `Open: none.` A retired number appears in neither the rules nor the
open list, and the issue says what happened to it.

**One pointer to the issue, in one place.** Repeating it per rule puts the same
fact in eight places.

## Where the two have to agree

Read the issue and the router side by side at the end of every pass. Nothing
checks this.

| Check | The failure it catches |
|---|---|
| Every question marked settled has a rule with that number | An answer that reached the conversation and no file |
| Every rule traces back to a settled question | A constraint nobody was asked for |
| The rule states the same constraint the issue settled | Two records that drifted, with the router winning by being read every turn |
| No rule carries reasoning the issue lacks | The why living in the file that gets skimmed |

## Running it again, when something is reversed

A constraint locked in month one and reversed in month six is when the record
earns its keep. Both files change in the same pull request.

1. **The issue first.** The question's status becomes reversed, with what
   reversed it. The measurement goes in a comment, dated, because evidence is
   append-only. The body then says the new answer.
2. **Then the rule**, rewritten under its own number. No "this used to say".
3. **The commit body says why**, under rule 13, because `git blame` is the path
   from a line back to its reason that never breaks.

A constraint dropped with nothing replacing it: delete its rule, add its number
to neither the open list nor another rule, and say in the issue what retired
it.

Anything already built against the old rule is separate work. File it, and say
in the pull request body that it exists.

## How this and `adopt` stay out of each other's way

`bin/adopt` renders a project's `CLAUDE.md` from its answers and then never
touches it again. The file carries no manifest row, and `seed_router` reports
`present` and returns for any router that exists. An update of the scaffolding
cannot overwrite a rule this skill wrote, and `tests/test_adopt.py` asserts
that against a router with a rule appended.

Three things follow.

**Edit one section.** Everything outside `## 1 to 8` down to `## 9.` was
rendered by `adopt`, and rewriting it puts the project's copy of rule 0 or rule
24 out of step with the template's, with nothing to detect it.

**A newer template router reaches an adopted project through nobody.** When
somebody applies one by hand, the project's own rules get carried across first.
They exist in that file and nowhere else.

**On a router `adopt` reported `present`**, the project wrote its own file. Its
constraints are already in it, in its own words. Ask where they live, and put
the section where the operator says, rather than appending a second set of
rules to a file that already has one.

## Excuses

| Excuse | Reality |
|---|---|
| "The codebase answered question two." | It answered what somebody built. A constraint is their decision, and nobody has been asked. |
| "I wrote the router section and skipped the issue." | The reasoning is then in a transcript, and the first reversal has nothing to reverse against. |
| "Nothing was settled, so I wrote nothing." | The issue is the output of that pass. Rule 22 asks for six open questions with costs on them. |
| "All eight, in the first session." | Eight constraints settled before anything exists means most of them were guessed. Settle what is real, leave the rest open. |
| "The operator said probably." | A probably is an open question with a name on it. It stays in the issue and out of the router. |
| "It matters to me, so it is rule 4." | Rule 0 has a layer for that. `.agentkit/local.md` for one person, `.agentkit/team.md` for two. |
| "I renumbered so the set reads 1, 2, 3." | A citation in a commit from last month now points at a different constraint. |
| "The rule changed, so I rewrote the issue and dropped the old answer." | Rule 23 keeps the evidence in a comment. Deleting it invites the same experiment again. |
