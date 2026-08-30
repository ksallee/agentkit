# How we work

Rules 10 to 19 and 21 to 23, with the reasoning behind each. They apply to
people and to agents equally, and a session that skips them has not done the
work. The rest of the set is in [`../../CLAUDE.md`](../../CLAUDE.md), which
loads every turn: rule 0 for the three layers, 1 to 8 for whatever the project
locked before it wrote code, 9 for probes, 20 and 24 for every piece of output.

**Two people read this repository, and neither one remembers what the other
settled.** That is the argument under every rule below. The issue body is the
record because whoever picks the work up was not in the session that changed
it. A commit body says why because the pull request that explained it scrolls
out of reach in a month. A stated preference goes into a file because a
transcript gets read once. An agent is the same reader at the extreme: it
arrives with no memory of last week and acts on whatever it is handed.

Rule 0 sets which of the three layers wins. This file is the shipped layer, so
`.agentkit/team.md` overrides it on a project convention and
`.agentkit/local.md` overrides it on taste. A rule below that sends its default
to the team layer does so because the answer is one nobody can hold privately.

Every word committed follows [`STYLE.md`](STYLE.md).

## What a machine checks

A rule with no mechanical consumer decays into a convention people follow when
they remember. Rules 17 and 24 are checked here today, by `bin/verify` over
`.agentkit/gates.toml`. The rest of the table is the design, and #10 is the
process job that asserts it:

| Rule | Asserted by |
|---|---|
| 13, 15, 16, 19, and the branch name in 11 | `.github/workflows/process.yml`, over the pull request body, its labels and its commit subjects |
| 12, no force-push | `.github/workflows/process.yml`, comparing the sha before each push against the sha after it |
| 17, the gates | a runner, over everything `.agentkit/gates.toml` declares |
| 23, the body is the record | `pick-work`, which reads issue bodies and refuses to read comments |
| 24, style | a style checker over every tracked file, and the process job over the pull request body and the commit subjects |

A project whose `.github/` has not been seeded has none of these, and a person
reads all thirteen rules instead.

What no check reaches, and why: whether an issue existed before the work
started (10), whether a body reached `gh` as a file (14), whether the label
list was read before labels were applied (15, only the result is visible),
whether the merge was permitted (18, the permission is a sentence in
`.agentkit/team.md` and a machine cannot tell an approved merge from an
impatient one), whether a reader would expect everything in the pull request
(20), whether a preference stated in a session was written down (21), and
whether an issue body is honest and current (22, 23). A person reads those.

## Roles

**This file names no roles.** A role is a line in one person's
`.agentkit/local.md` that selects one guide out of `docs/` and excludes the
others. That selection is the whole mechanism. `adopt` seeds the guides as
skeletons, and a skeleton nobody fills is a role the project does not have.

Add a role when a named risk makes one kind of call somebody's job. mac-hours
names a designer because its unassigned inbox screen was diagnosed as the thing
that decides whether the tool survives: the tracking works on day one, the
habit of opening the app does not, and a triage screen that is unpleasant to
use is a tracker that quietly stops being accurate six weeks in. That is a
design problem with an engineering consequence, so the design call is owned
rather than applied at the end. A project with no such finding ships no such
role, and three empty guides are three files nobody reads.

**A role never gates a command** (mac-hours#133). Every skill is available to
everybody, and a command checks the preconditions it needs and prints the fix
when one is missing. Somebody who came for the schema and now wants a different
colour is doing design for twenty minutes, and a role gate puts a wall exactly
there.

Where two people in different roles disagree, `.agentkit/team.md` says who wins
on what.

---

## The loop

```
issue -> branch -> work -> PR -> review -> squash merge
```

```bash
gh issue create --title "..." --label "area: rules,enhancement" --body-file /tmp/issue.md
gh issue edit 12 --add-assignee @me
git fetch origin && git switch -c 12-short-slug origin/main
gh pr create --body-file /tmp/pr.md
```

### 10. Every change starts as a GitHub issue

Three exceptions, stated rather than winked at:

1. **Somebody is driving a live session.** When a person is instructing change
   by change, filing an issue before "label the sort control" is friction
   nobody asked for. Work on a branch, then file the issue afterwards and
   reference the commits.
2. **It is broken today and the fix is obvious.** Fix it, then file
   retroactively.
3. **It is a capture change under rule 21**, writing down a preference somebody
   stated. Branch, open the pull request, merge on green. No issue at all.

Planned work, anything another person picks up, and anything touching what
rules 1 to 8 locked still starts as an issue. A rule that gets ignored is worse
than a rule with an exception, because silent non-compliance teaches the next
reader that the rules are decorative.

A capture change has no issue, so its pull request body opens with `Capture
change, no issue.` on a line of its own in place of `Closes #N`. That line
waives rules 11, 13 and 16 in the process job, and it puts the exception in the
record rather than in a reviewer's memory.

The issue is where transient thinking lives: the spec, the repro, the options
considered and rejected. Permanent knowledge goes in `docs/`.

Search first: `gh issue list --state all --search "<keywords>"`.

A good issue titles the **outcome**, never the activity. *"Git worktrees of one
repository are ingested as several, so every commit count multiplies"*
(mac-hours#123) tells a reader what is wrong and what it costs. *"Look at the
git ingest"* tells them where somebody was going to poke. The body carries
repro steps for anything behavioural, `file:line` for anything already located,
and an explicit **out of scope** where the surrounding area is messy.

### 11. Assign the issue to yourself, then branch off `origin/main`, named after the issue number

`12` or `12-slug`. The process job checks that the branch number matches an
issue the pull request body closes or advances under rule 16, and that somebody
is assigned to it.

```bash
gh issue view 12 --json assignees      # is anyone on it already?
gh issue edit 12 --add-assignee @me
git fetch origin && git switch -c 12-short-slug origin/main
```

That one command works in a plain checkout and in a worktree. `git checkout
main` works in only one of them:

```
fatal: 'main' is already used by worktree at /Users/you/dev/project
```

Cutting from `origin/main` drops the local branch out of the path, so a stale
local `main` cannot put the work behind. Five agents in one parallel wave hit
the worktree failure on the same afternoon (#57).

**Parallel work happens in a git worktree under `.claude/worktrees/`.** One
worktree per branch keeps two sessions out of each other's working tree, and
`main` stays checked out in the original clone. The directory is gitignored
(#47).

**Read `git status` in the clone before you switch, and cut a worktree while it
is dirty.** `git switch -c` carries every uncommitted file onto the new branch,
where the next `git add` commits it under your issue number. So the switch
route belongs to a session alone in a clean tree, and a session that might
overlap with another one branches by cutting a worktree:

```bash
git worktree add .claude/worktrees/12-slug -b 12-slug origin/main
```

A worktree collision announces itself. Carrying another session's files across
is silent: four agents ran in this clone on 2026-08-30, one swept three files
belonging to three other sessions into a commit on its own branch, and the
recovery happened because two of them were reading `git status` closely (#150).

Assignment claims the work. Pushing a branch does not, and with two people and
an agent each, the same issue gets started twice.

**One branch may close several issues.** When they are small and related, or
when you hit a bug while working on something else, fold it in: name the branch
after the main issue, file the others, and list every one in the pull request
body. Two branches for two one-line fixes is ceremony. The body carries the
traceability the second branch would have bought.

### 12. Keep the branch fresh by merging `main` in

`git merge origin/main`. Never rebase a pushed branch, and never force-push.
Somebody else may have it checked out, and an agent may be mid-session on it.
The process job compares the sha before each push against the sha after it, and
fails when the first has stopped being an ancestor of the second.

### 13. Commit subject = issue title + issue number

No type prefix. Where the issue titles an action, the subject is imperative;
where it titles a defect, the subject names the defect, because the subject is
the title.

```
Inbox: a plain click on a row ticks its checkbox #90
```

`git log --oneline` then reads as the board, which is what makes a subject
worth constraining at all.

**The body says why, and what you rejected.** A body restating the diff is
wasted. A body saying *"dropping a window event that overlaps AFK lost 40
minutes of real work on any day with a lunch break inside a long editor
session"* (mac-hours#2) is the reason the change exists. `git blame` is the one
path from a line of code back to its reason that never breaks: the issue
closes, the pull request scrolls away, the branch is deleted, and the commit
stays attached to the line. Rule 22's instruction to record the measurement
rather than the conclusion applies here for the same reason.

**An agent-written commit carries two attribution trailers, until
`.agentkit/team.md` says otherwise.**

```
Claude-Session: https://claude.ai/code/session_<id>
Co-authored-by: <the model, as it names itself> <noreply@anthropic.com>
```

A commit made by hand carries neither. No gate reads either line and nothing in
these rules depends on one. The session line leads from a merged commit back to
the conversation behind it, after the pull request has scrolled away.

A project writes its own answer under `## Conventions this project settled` in
`.agentkit/team.md`, and rule 0 gives that layer the field. An empty section
means the two lines above.

### 14. Pass issue and pull request bodies to `gh` via `--body-file`

Never inline. Shell quoting mangles a body that contains backticks, quotes or a
`$`, and the file is what survives a retry after the command fails.

### 15. List labels before applying them

```bash
gh label list
gh issue create --title "..." --label "area: rules,bug" --body-file /tmp/issue.md
gh pr edit 12 --add-label "area: mechanism" --add-label "bug"
```

One `area:` label plus at least one kind label, on the issue and on the pull
request both. `effort:` is a third axis and never counts as the kind. The
taxonomy grows as the project does, which is why the list gets read rather than
remembered.

Both objects carry them because both sit on the board and get filtered
separately, and they can disagree. The process job reads the pull request's own
labels, so a bare pull request fails rule 15 with its issue labelled correctly.

### 16. Open a pull request whose body starts with `Closes #12`

The keyword has to be in the body. A comment cross-references and does not
close on merge.

**Work that advances an issue without finishing it opens `Advances #17`.**
GitHub gives that word no closing power, so the issue survives the merge and
goes on being the record of what is left. Two things come with the opening: a
`## Remaining` section in the body naming the unfinished part, and the issue
body edited under rule 23 in the same pull request. Rule 11 is unchanged, and
the process job reads the advanced number for the branch and the assignee.

Advance an issue when the half already built is worth reviewing on its own.
Where the second half turns out to be separate work, file it as its own issue
and close this one.

State in the body **what you verified and what you did not**. "Tests pass" does
not verify a UI change: say which page you loaded, what you clicked and what
you saw. For anything numeric, say which number you checked by hand and against
what.

Merge with **squash**, so `main` stays linear at one commit per issue, and
delete the branch. **Remove the worktree first**, because `git branch -d`
refuses a branch any worktree has checked out and the merged branch's own
worktree is holding it:

```bash
git worktree remove .claude/worktrees/12-slug
gh pr merge 12 --squash --delete-branch
```

Where the merge runs from decides which way it fails, not whether it does. In
the other order `--delete-branch` fails after the merge has already landed, and
the remote branch survives; `## Easy to get wrong` carries the recovery.

### 17. Every gate declared in `.agentkit/gates.toml` passes before you say you are done

The rule names no command. A runner runs what the file declares, in order,
and CI runs the same file. Anything else is a second copy that drifts.

That duplication is measured. In mac-hours the five gate commands appeared in
seven files, and three of the copies had already disagreed with each other by
the time mac-hours#143 moved them. STYLE.md states the general form: a fact in
two files is a fact that will disagree with itself.

**A gate you say passed without its output in the session did not pass.**
Reporting a green run from memory, or from a run before the last edit, is a
false claim about the state of the branch. Run it, then say what it printed.
This is stronger than listing commands and trusting they were run, and it is
taken from superpowers' `verification-before-completion`, read at v6.3.0 on
2026-08-29.

### 18. Merging your own pull request is a decision somebody has to have made

Opening it is the work. Merging is a judgement about whether it should land,
and with two people there is a real reviewer to make it.

**The default lives in `.agentkit/team.md`**, because it is a thing two people
have to agree on. A project can say that everything waits for a review, or that
an agent may merge on green, or that some class of change may. Do not infer the
answer from what happened last time.

One exception holds wherever the rest lands. A **capture change** under rule 21
merges on green: holding a one-line correction to a skill for a review round
costs more than the correction, and until it lands the person repeats
themselves next session. The pull request is still the record. The wait is the
disproportionate part.

### 19. Never commit what the project captured about a person

In mac-hours every window title and every URL in the database is a record of
what one person read, typed and browsed. Whatever the equivalent is in this
project, the ignores cover it and its sidecars, and keeping that true is part
of the work.

A test fixture is hand-written or scrubbed, never a slice of a real store. This
is the mistake that survives rewriting history, because a pushed object stays
reachable through the pull request refs after the branch is gone, so the
process job fails on a data file appearing anywhere in the diff.

A project that captures nothing about anybody keeps the fixture half. A
scrubbed fixture is also how a real credential stays out of the tree.

### 21. Capture a stated preference in the surface that will read it next

When somebody says how they want something done, write it down, in the layer
rule 0 assigns it to: the skill or command itself for how a skill behaves,
`.agentkit/local.md` for how work is delivered to one person,
`.agentkit/team.md` for a convention the two of them share, these rules for
something that would hold in any project. A preference living only in one
session's transcript is one they have to repeat forever.

Two guards. **Never infer a rule from a single instruction.** "Branch it this
time" is not "always branch". **Never promote one person's preference into the
shared layers**: the test is whether it applies to everybody, and
`.agentkit/local.md` is where it goes when it does not.

A capture change skips the issue (rule 10) and merges on green (rule 18). It
still gets its own branch and pull request, because the pull request is the
record.

### 22. An issue opens with what must be settled before work starts

Lead with the questions whose answers change the shape of the work, ahead of
any proposal. An unverified assumption. A decision only one person can make. A
dependency on data that does not exist yet. Say which of them are cheap to
answer, and who can answer each one. A question with no answerer is a musing
and gets deleted.

The grey areas are known at filing time and almost never written down. An issue
that reads as ready when it is not is how somebody spends a day building the
wrong thing, and two sentences from whoever filed it would have prevented that.
mac-hours#5 is the shape to copy: seven open questions, each with what it would
cost to answer, filed before any of the product was drawn.

Where an approach was tested and rejected, record the measurement rather than
the conclusion. *"Merging on app alone collapsed four projects into one editor
row"* (mac-hours#2) stops the next person repeating the experiment.
*"Merging on app does not work"* does not.

### 23. The issue body is the record, and it is edited in place

An issue is read once, by somebody deciding whether to start it, and that
reader gets the body. **When something is settled, changed or ruled out, the
body changes to say so**, and the question it answered stops being listed as
open.

The failure this prevents is specific and it has happened. A mac-hours issue
was filed with five open questions. Six comments settled four of them, reversed
a conclusion reached in the third, and added two questions nobody had thought
of. The body still read as it had on day one. Anybody picking the issue up off
the board saw a question that had a measured answer and a settled list that was
two entries short. mac-hours#169 and #170 are what came out of it.

Comments still carry the things worth having a date on:

- a measurement, with the numbers and the command that produced them
- a probe result
- a conclusion reversed, and what reversed it

Each of those is evidence, and evidence is append-only. The body then changes
to match, so the comment holds the measurement and the body holds the answer.
Editing the body to say "the install path cannot pin a version, measured"
leaves the comment that measured it in place.

The cost of the alternative is paid by the reader every time. The rule earns
its place when something mechanical depends on it: in `mac-hours` the
`pick-work` skill reads bodies and refuses to read comments, which stays
correct only while this rule holds. A project with no such consumer has a
convention rather than a rule, and should expect it to decay.

---

## Easy to get wrong

**Retarget a stacked pull request before merging the one below it.** Squash
merging with `--delete-branch` deletes the base branch, and GitHub closes every
pull request pointing at it. A closed pull request cannot be retargeted and
cannot be reopened while its base is missing, so recovery means pushing the
deleted branch back, then reopening, then retargeting. Do it in this order:

```bash
gh pr edit <upper> --base main    # every PR stacked above, first
gh pr merge <lower> --squash --delete-branch
git merge origin/main             # in the upper branch, never rebase
```

After a squash merge the upper branch still carries the original commits, so
merging `main` in resolves cleanly against the squashed equivalent.

**Wait for the checks to finish before merging.** `gh pr checks` prints nothing
on a pull request whose runs have not been created yet, so a count of zero
failures is also what a pull request with no checks at all looks like.

**`gh pr merge` exits non-zero after the merge has landed.** Run from a
worktree it fails on the local step that follows the merge, in one of two
places depending on which branch is where:

```
fatal: 'main' is already used by worktree at /Users/you/dev/project
failed to delete local branch 12-slug: cannot delete branch '12-slug' used by
worktree at /Users/you/dev/project/.claude/worktrees/12-slug
```

Neither says what happened to the merge, and the merge succeeded. Ask the
server rather than the exit code, and finish the cleanup by hand:

```bash
gh pr view <n> --json state        # MERGED, whatever the exit code said
git push origin --delete <branch>  # --delete-branch never got this far
```

Rule 16's ordering, the worktree removed before the merge, avoids both. This
is here for the reader who already has the error in front of them. Four actors
hit it in one session on 2026-08-30, and each diagnosed it from scratch,
because the error text appeared nowhere in the repository.
