---
name: wrap-up
description: End a session properly. Checks the repository was left clean, reads the prose the session added against STYLE.md, and writes every preference the session stated into the file that reads it next. Use when someone says "wrap up", "call it a day", "let's stop here", "can I exit", or invokes `/done`.
---

# Wrapping up

Rule 21 in `docs/development/WORKFLOW.md`: a preference stated in a session and
written nowhere is one the operator repeats forever. This skill checks that
none was left behind, and that the tree is somewhere `/work` can start from
tomorrow.

## 1. The tree, left clean

Run all of it. Fix what is red before saying anything else.

```sh
bin/verify                            # rule 17, every gate declared
git status --short                    # nothing uncommitted
git log origin/main..main --oneline   # nothing unpushed
gh pr list --state open               # nothing waiting that should have merged
gh run list --branch main --limit 1   # main is green
```

Report what any running agent is doing. Stopping one silently loses its work.

### The worktrees and the branches

An agent session leaves a worktree under `.claude/worktrees/` and a branch
behind it, and the work that made them clears neither. They accumulate until
`git worktree list` runs to twenty. Clear both at the end of every session
without being asked. This is the one step here that destroys something, so each
delete gets a check first.

```sh
git worktree list --porcelain | awk '/^worktree /{print $2}' | grep '/worktrees/'
```

Remove those, run `git worktree prune`, then take every local branch except
`main`:

| State | Check | Then |
|---|---|---|
| Ancestor of `main` | `git merge-base --is-ancestor <b> main` | Delete |
| Squash merged | `gh pr list --head <b> --state all --json state` | Delete on `MERGED` |
| No pull request | Find what carried the work under another name | Say what you found |
| Anything else | | Keep it, and name it in the recap |

A squash merge leaves the branch a non-ancestor of `main`, so ancestry alone
answers nothing and GitHub gets asked. Two guards. A worktree holding
uncommitted changes gets its `git diff` written to the scratchpad first, and
the recap says where. And a stale worktree's files compared against today's
`main` decide nothing: `main` moved, so they differ either way.

## 2. The prose the session added

`bin/check-style` catches six spellings. Voice, restatement and padding are a
reading. Read the diff against `docs/development/STYLE.md`: its `## Voice`
table names the habits, and the figures under it place a file.

```sh
git diff origin/main...HEAD -- '*.md' '*.py' '*.ts' '*.svelte'
```

Judge each instance. A count places a file and settles nothing about a
sentence: four uses of `never` in one file can all earn their place, and a
regex flags all four.

Fix what you find on the branch you are on, or as a capture change once the
work merged. Say what you cut.

## 3. The session, against the surfaces

Read the conversation from the top. List every sentence where the operator said
how they want something done, settled a question, or corrected a run.

**The bar: something steered a run wrong.** Folding in everything a session
learned edits recorded files on every branch, and those files then conflict on
every merge. An explicit preference clears the bar. So does a correction. An
observation does not.

Route each one to the file that reads it next.

| What was said | Where it goes |
|---|---|
| A question settled about an open issue | that issue's body, edited in place (rule 23) |
| How a skill behaves, what it asks, what it refuses | `.claude/skills/<name>/SKILL.md` |
| The wording or the steps of a slash command | `.claude/commands/<name>.md` |
| A convention two people have to agree on | `.agentkit/team.md` |
| One person's taste | `.agentkit/local.md` |
| Something that would hold in any project | `CLAUDE.md`, or `docs/development/WORKFLOW.md` for how work is opened and reviewed |

**Those six rows are rule 0's layers. The rest of the table comes from the
project.** `bin/surface list` names the surfaces earlier sessions wrote, and
the tree names what nobody has recorded yet: a role guide under `docs/`, a
design skill, a router. Read both before routing.

**A project with no `.agentkit/team.md` or no `.agentkit/local.md` keeps the row
and reports the file as absent.** Rule 0 reads an absent personal layer as
nobody having been asked yet. A shared convention with no team file waits for
one. It does not go into somebody's personal file, and no seventh location gets
invented for it.

The issue row is the one this skill misses most. Four questions answered in a
session is four decisions, and the next reader sees none of them until the
bodies say so. Check every issue discussed, including any nobody worked on.

Two guards from rule 21. One instruction is one instruction: "branch it this
time" says nothing about next time. And one person's preference stays in the
personal layer until it applies to everybody.

**Record every surface you wrote.**

```sh
bin/surface record <name> <path>
```

The registry answers which files here capture a preference and when each was
last written, so the table above grows as the project does. A surface written
and left unrecorded is one the next `/done` cannot route to. The registry is
gitignored and holds no decision: losing it costs the list, and every decision
stays in the file it was written into.

## 4. The reverse check

Anything the session changed that a document describes: does the description
still hold? Counts and lists in `CLAUDE.md` and `WORKFLOW.md`. A skill saying
"until #N lands" where #N landed. A command a skill quotes whose flags moved.

## 5. Say what happened

Four lines, in order: what merged, with numbers; what is open and what it waits
on; what was captured and where, plus what was already there; and anything the
operator needs before the next session, such as a machine setting that changed
or real data written during verification.

Then stop. `/work` is the next session's first move.

| Excuse | Reality |
|---|---|
| "Nothing was stated this session." | Read it back before saying so. A settled question is a decision. |
| "It is in the recap." | The recap scrolls away. Rule 21 names a file. |
| "There is no `team.md`, so it went in the personal layer." | The other person then never sees it. Report the absence. |
| "I wrote the file, recording it is bookkeeping." | An unrecorded surface is one the next `/done` cannot see. |
| "The branch is no ancestor of `main`, so its work never merged." | A squash merge always looks like that. Ask the pull request. |
| "The gates were green earlier." | Rule 17: output in this session, or they did not pass. |
