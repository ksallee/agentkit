---
name: wrap-up
description: End a session and leave the tree where the next session can start. Covers the gates, the worktrees and merged branches an agent session leaves behind, the prose the session added read against STYLE.md, every preference the session stated routed to the file that reads it next and recorded with `bin/surface`, the documents the session invalidated, and the recap. Use when someone says "wrap up", "call it a day", "let's stop here", "can I exit", or invokes `/done`.
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

**Then ask what survived on the remote.** Everything above is local, and a
merged branch can outlive its merge on GitHub: `gh pr merge --delete-branch`
fails on its local step when it is run from a worktree, and the remote deletion
is what it never reaches. Nothing else looks for them, and they accumulate. The
first full run of this check in agentkit, on 2026-08-30, found twenty-eight.

`--limit` is the whole answer here and it is easy to get wrong. The same check
run at `--limit 20` on the same afternoon reported sixteen, because it reads
that many merged pull requests and not that many branches. Set it past the
repository's merged count, and treat a number equal to the limit as a truncated
answer rather than a total.

```sh
git fetch -p -q origin
comm -12 \
  <(gh pr list --state merged --limit 200 --json headRefName -q '.[].headRefName' | sort -u) \
  <(git ls-remote --heads origin | sed 's|.*refs/heads/||' | sort -u)
```

One `ls-remote` for the whole remote, intersected with the merged list. Asking
per branch instead is one network call per merged pull request, and at two
hundred it runs past two minutes and gets killed, which looks like a clean
remote and is not.

Delete each with `git push origin --delete <b>`. A branch here is debris by
definition: its pull request is merged and the branch is still on the remote.
`docs/development/WORKFLOW.md` under `## Easy to get wrong` carries the failure
that leaves them.

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

**Report an absent `.agentkit/team.md` or `.agentkit/local.md` in the recap,
whether or not anything routed there this session.** Rule 0 reads an absent
personal layer as nobody having been asked yet, and a session that reads it as
"no preferences" says nothing and asks nothing, so the next session starts from
defaults for the same reason. Write no stub: an empty file and a person nobody
has asked look identical, and rule 0 depends on telling them apart.

A shared convention with no team file waits for one. It does not go into
somebody's personal file, and no seventh location gets invented for it.

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
on; what was captured and where, plus what was already there and which of rule
0's layer files is still absent; and anything the operator needs before the
next session, such as a machine setting that changed or real data written
during verification.

Then stop. `/work` is the next session's first move.

| Excuse | Reality |
|---|---|
| "Nothing was stated this session." | Read it back before saying so. A settled question is a decision. |
| "It is in the recap." | The recap scrolls away. Rule 21 names a file. |
| "There is no `team.md`, so it went in the personal layer." | The other person then never sees it. Report the absence. |
| "Nothing routed to `.agentkit/local.md`, so there was nothing to report." | Rule 0 reads its absence as nobody having been asked. The recap says it is missing. |
| "I wrote an empty `.agentkit/local.md` so the file exists." | A stub and an unasked person then look the same, and rule 0 can no longer tell. |
| "I wrote the file, recording it is bookkeeping." | An unrecorded surface is one the next `/done` cannot see. |
| "The branch is no ancestor of `main`, so its work never merged." | A squash merge always looks like that. Ask the pull request. |
| "The gates were green earlier." | Rule 17: output in this session, or they did not pass. |
