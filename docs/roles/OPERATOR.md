# Operator's guide

Owns what the project is for, and the calls only they can make. Read
`CLAUDE.md` first. Everything below assumes the three layers rule 0 sets out,
because most of this role is deciding which layer an answer belongs in.

## What only you can answer

Four decisions have no correct default, and an agent that guesses one of them
is guessing on your behalf.

| Decision | Where it lives | What goes wrong without it |
|---|---|---|
| Rules 1 to 8 | `CLAUDE.md` | somebody invents a constraint and it reads as settled |
| Which gates run | `.agentkit/gates.toml` | rule 17 and CI disagree, and the rule stops meaning anything |
| Who merges | `.agentkit/team.md` | an agent merges its own work, or waits forever |
| `shaping` or `building` | `.agentkit/phase.json` | work gets picked by the wrong criteria |

Answer them once, in the file, and they hold across sessions. An answer given
in a conversation is one you give again next week.

## Say how you want work delivered, once

`.agentkit/local.md` is your file, gitignored, and it wins on taste: how much
you want to read, whether you want the diff or the summary, what "done" means
to you, which role guide applies to which task, what is off limits. Its absence
means nobody has been asked.

Rule 21 puts the burden on the session, so anything you state should end up in
a file without you asking. When it does not, say so, because a preference
living only in a transcript is one you repeat forever.

## The bar for what goes where

Rule 0 splits it three ways, and the split is worth holding.

- Something two people have to agree on goes in `.agentkit/team.md`. One person
  opting out of the test suite is a decision, and it belongs there.
- Your own taste goes in `.agentkit/local.md`. Promoting it to the team layer
  makes somebody else live with it.
- Something that would hold in any project goes in `CLAUDE.md` or
  `docs/development/WORKFLOW.md`.

## Read the plan before anything writes

`adopt` prints a plan and writes nothing until you say so. So does any command
that replaces a file. The plan exists to be read by somebody who can say no,
and a session that runs the plan and the write in one turn has skipped that.

## QA is yours, after the fact

Where the team layer lets an agent merge on green, the gates said the code runs
and nobody said it was right. Open the thing, use it, and file what you find as
an issue. A defect found afterwards is a new issue and the branch is already
off the board, and permission buys exactly that.

## Where it stopped

The most useful thing this role produces is a record of where the scaffolding
stopped working. A step assuming a screen the project lacks. A skill asking a
question the team layer already answered. A role guide selected from nothing. A
rule citing a file that does not exist.

File each one. A run that produces no issues means the run was too small.

## The failure mode to watch for

Answers drifting out of the files and back into conversation. It starts with
one question answered in chat because it was faster, and it ends with a project
whose real rules live in a transcript nobody can search. When you catch
yourself answering the same thing twice, it belongs in a file, and rule 21
names which one.
