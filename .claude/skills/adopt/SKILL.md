---
name: adopt
description: Seed the agentkit scaffolding into a project, or update a project that already has it. Covers the answers the team layer and the router need, the plan somebody reads before anything is written, what a rerun replaces and what it keeps, and what to do when the project already has its own CLAUDE.md. Use when someone says "adopt agentkit here", "set this project up", "update the scaffolding", or asks what a rerun would change.
---

# Adopting the scaffolding

`bin/adopt` owns the copying and the hashing. This skill owns the questions.
Never write `.agentkit/manifest.json` by hand, and never copy a seeded file
with `cp`. An improvised manifest lies on the next update.

## Say the request back before anything else

The request arrives as a sentence in somebody's own words: "adopt agentkit
here", "set up the repo in ~/dev/thing", "update the scaffolding". Two
phrasings of one intent can land on different paths and nothing downstream
reports that they did.

Say back two things and wait for a yes:

- **The directory**, as an absolute path. "Here" is the session's working
  directory, and a session started somewhere else adopts somewhere else.
- **First adoption or update**, and what said so. `.agentkit/manifest.json`
  present means the project was adopted before and this run replaces seeded
  files. Absent means nothing here has been seeded.

`bin/adopt` reads the manifest for itself, so a misreading costs what the
session does around the tool. A first adoption needs all six answers before
anything is written. An update has them in `.agentkit/team.md` already, and
what it needs read back is which files a rerun replaces and which it keeps. The
wrong directory means every one of those questions was asked about the wrong
project.

## Preconditions

Check these and print the fix. Don't work around them.

| Needs | Check | Fix |
|---|---|---|
| An agentkit checkout | `ls $AGENTKIT/bin/adopt` | `git clone git@github.com:ksallee/agentkit.git` |
| python3 | `python3 --version` | Ships with macOS. |
| The target is a git repository | `git -C <project> rev-parse --git-dir` | `git init`, so a bad adoption is one `git checkout` away. |

The last one is a precondition. Adoption replaces files, and a project with no
history has no way back.

## The six answers

Ask all six in one pass. Five carry a default worth accepting.

| Answer | Flag | Default |
|---|---|---|
| Which gates the project runs, and what CI installs | `--pack python\|typescript\|python+typescript\|none` | **None. This is the one it will not guess.** |
| The project's name | `--name` | The directory name. |
| One line saying what it is | `--summary` | Left unanswered in `team.md` and in `CLAUDE.md`, marked as such. |
| Who reviews and who merges | `--merge` | The author does not merge their own pull request. |
| Shaping or building | `--phase` | `building` when the target has a commit, `shaping` when it does not. |
| Where the design pipeline gets references | `--references curated\|refero` | `curated`. |

**The pack has no default and adopt refuses to write the team layer without
it.** A gate list naming a command the project does not run makes rule 17
disagree with CI, and a rule CI contradicts is worse than an absent one.
Guessing `python` from a `pyproject.toml` gets every project with a `web/` half
wrong. Ask.

The seeded gate list is a starting point that nothing verified. After the
write, run `bin/verify` once and correct `.agentkit/gates.toml` where a gate
fails for the wrong reason. The seeded workflow runs the same command, so a
gate that passes here passes there.

The pack also picks what CI installs: uv for every pack, plus node, pnpm and an
install step for a pack with pnpm gates. A gate added later that needs another
tool needs a step in `.github/workflows/gates.yml`.

The name and the summary reach two files: `.agentkit/team.md` and the project's
`CLAUDE.md`, which an agent loads every turn. A summary nobody gave leaves both
saying so.

### References, and why it is opt in

`refero` means the design pipeline queries refero.design, a third-party
service, for its reference list. `curated` means it reads a list this project
maintains. Say that plainly and let the operator decline: the whole pipeline
works on `curated`, and a project can switch later by editing one row in
`.agentkit/team.md`. Adopting scaffolding is not the moment to sign somebody up
to an outside service by default.

The other row in that table, `surface`, says where a finished design lands
(`canvas`, `file` or `none`). `adopt` seeds it unanswered, so somebody picks
one before the design skills run.

## Run the plan first, always

```sh
python3 $AGENTKIT/bin/adopt /path/to/project
```

That writes nothing. Read the outcome for every file back to the operator
before proposing a write.

| Outcome | What it means | What a write does |
|---|---|---|
| `written` | No file there | Writes it |
| `unchanged` | Byte identical to the template | Nothing |
| `updated` | Matches the manifest, so it is the template's own older copy | Replaces it |
| `kept` | Matches neither, so somebody here wrote it | Writes the template version and moves theirs to `<path>.local` |
| `removed` | The manifest records it, `seeds.json` no longer names it, and it still hashes to the recorded value, so the bytes are this template's | Deletes it, drops its manifest row, and takes any directory it emptied |
| `orphaned` | Same, except the bytes differ, so the project owns them now | Nothing. The file stays, the row stays, and the next run reports it again |

An orphan under `.claude/skills/` keeps loading and competes for its
replacement's triggers, so read every `orphaned` line back and offer to merge
or delete each one by hand.

## What runs in CI

`.github/workflows/gates.yml` and `process.yml` are seeded, and they are the
only thing that runs any of this without a person.

**The gates workflow names no gate.** One step, `bin/verify`, which reads
`.agentkit/gates.toml`, so the project edits its gate list and CI follows with
no second edit. The runner writes its table to the run summary, so a failing
gate names itself there. What the pack decides is the toolchain: uv always,
because `bin/verify` runs under it, plus node, pnpm and one `pnpm install` per
directory a pnpm gate declares.

**The process workflow runs five checks and reports two absent.** Rules 11, 13,
16 and 24 are code and work on the first pull request. Rule 15's label taxonomy
and rule 19's forbidden paths read `.agentkit/process.toml`, and `adopt` seeds
no such file, because the area prefix is the project's own answer. Both report
`absent` in the run summary until somebody writes it. Say that to the operator
after the write, and offer to write the file from `gh label list`.

## The router is seeded once and replaced never

`CLAUDE.md`, the three `.agentkit/` files and the two workflows are rendered
from the answers rather than copied, so they carry no manifest row and no rerun
touches them. A workflow this template replaced would leave the project's
version at `gates.yml.local`, which GitHub runs nowhere, so the project would
be running this template's copy without being told. Two outcomes, and neither
writes over anything:

| Outcome | What it means |
|---|---|
| `seeded` | Nothing was there. `adopt` wrote it from the answers |
| `present` | A file is there. `adopt` left it exactly as it found it |

## The ignore file is the one merge this tool performs

`.gitignore` gets a block between `# agentkit start` and `# agentkit end`,
rewritten on every run, with every line outside it left alone. Git reads each
line of a `.gitignore` on its own, so the block sits beside whatever the
project already ignores and neither half changes what the other means. Five
lines go in: `.agentkit/local.*`, which rule 0 requires, `.claude/worktrees/`,
and the `design/*.dc.html`, `design/*.classes.html` and `design/canvas.json` an
artboard run writes.

| Outcome | What it means |
|---|---|
| `seeded` | No `.gitignore` there. `adopt` wrote one carrying the block |
| `appended` | The project has one and it carries no block. The block goes on the end and no line above it moves |
| `unchanged` | The block is there and already says this |
| `updated` | The block is there and said something older. Only what sits between the markers is rewritten |
| `kept` | The file opens a block and never closes it. Nothing was written |

`kept` here writes nothing and leaves no sidecar, which is where it parts from
`kept` on a seeded file. The end marker is where a rewrite stops, so a guess at
it would delete the project's own ignores. Tell the operator to put the marker
back or delete the opening one, then rerun.

## The `skills` section names what the operator's own machine shadows

The report prints the personal skills root, then one `shadowed <name>` line per
skill this template seeds that the root already holds. Two skills of one name
both load and a typed `/name` reaches the personal copy, measured 2026-08-30 on
Claude Code 2.1.251 (#40), so each name on that list is a skill this run writes
into the project and nobody on this machine can reach by name. That directory
is read and never written to, and the run continues.

Read every `shadowed` line back and offer to rename the project's copy or move
the personal one aside. A line saying `probes/skill_precedence.py` did not load
means nothing was listed, so say that no collision was ruled out.

## When the project already has a CLAUDE.md

**This is a question, and the operator answers it.** `bin/adopt` prints
`present`, says what a seeded router would have carried, and stops. Nothing is
moved, nothing is overwritten, and no `.local` sidecar appears. A router is the
one file most likely to have been written by the project itself, and it is
loaded every turn by every agent working there.

Read their `CLAUDE.md` first, then put these four to them. Say which one you
would pick for this project and why, and take their answer.

| Option | What it costs | When it fits |
|---|---|---|
| **A managed block appended to their file** between two marker comments | Their file grows; a later update rewrites only what is between the markers | Their router is short and about their product, so the two do not overlap |
| **A sidecar theirs points at**, such as `docs/development/RULES.md` with one line in their router linking it | One more hop for a reader; their router stays theirs | Their router is long and they want it left alone |
| **A merge by hand**, section by section | An hour of somebody's attention, once | The two routers disagree about something real, so a machine would pick wrong |
| **Move theirs aside** to `CLAUDE.md.local` and seed | Their instructions stop loading the moment it happens | They said their router is stale and they want this one |

Two things to say out loud whichever they pick. A `.local` file is loaded by
nothing, so the fourth option takes their working instructions away until
somebody merges them back. And rules 1 to 8 are theirs: whatever their router
already locks about storage, precedence or scope belongs in those numbers, and
none of the four options moves it there for them.

## What `kept` costs, and say it out loud

On a project older than the template, every colliding file is `kept`, because
there is no manifest saying otherwise. A write then replaces the project's
`docs/development/STYLE.md` with the template's and leaves the project's copy
at `docs/development/STYLE.md.local`, which nothing loads. Measured
2026-08-29: the skill loader ignores a `.local` sidecar entirely.

So a first adoption of a mature project gives it almost nothing and takes
something real. Two honest routes, and the operator picks:

1. **Adopt the files that are absent, keep the rest.** Run with `--write`,
   then for each `kept` file merge by hand from the `.local` copy and delete
   the sidecar once it is merged. The manifest now says those bytes are the
   template's, so the next update reports `updated` and not `kept`.
2. **Adopt nothing yet.** Take the plan as a diff of two ways of working and
   file the merges as issues.

There is no mode that records the project's current bytes as the baseline.
That would make the manifest mean "these bytes were here once" instead of
"these came from the template". The two differ on the next run: `updated`
replaces a file freely, so the lie cashes out as a
silent overwrite of work nobody here wrote.

## Writing

```sh
python3 $AGENTKIT/bin/adopt /path/to/project --write --pack python \
  --name mac-hours --summary "Project-scoped time tracker."
```

Then, in the project:

```sh
git status --short
git add CLAUDE.md .agentkit .github docs .claude && git commit
```

The manifest is committed, so both people see the same adoption state.

## Updating later

The same command. A file nobody touched comes back `unchanged` or `updated`,
and a file somebody edited comes back `kept` with both names on the line. A
path this template stopped shipping comes back `removed` untouched and
`orphaned` edited, and those two only ever appear on a rerun. The
team layer and `CLAUDE.md` are seeded once and never rewritten, so an edit to
`gates.toml` or to the project's own rules 1 to 8 survives every rerun.

That cuts both ways. A newer router in the template reaches an adopted project
through nothing, so a change to the rules that travel is one somebody applies
by hand. Read the two files side by side when the template's rule set moves.

## Excuses

| Excuse | Reality |
|---|---|
| "The plan looked fine, I ran the write in the same turn." | Nobody read it. The plan exists to be read back by a person who can say no. |
| "I picked the pack from the lockfiles." | A wrong gate list makes CI and rule 17 disagree, which is the one failure this refuses to risk. |
| "I copied the file across and added the hash myself." | The manifest is the record of what the script wrote. A hand-written row makes the next `kept` a lie. |
| "The sidecar is there, so nothing was lost." | A `.local` file is loaded by nothing. Until somebody merges it, the project lost the file it was using. |
| "It only reported `kept`, so the run did nothing." | `kept` replaces the file. It is the loudest outcome, and it is why the plan is the default. |
| "The run said `orphaned`, so there is nothing to do." | The file stays and goes on loading. `adopt` reports it every run because a person has to merge it or delete it. |
| "Their `CLAUDE.md` was thin, so I moved it aside." | Four options, and the operator picks. Moving theirs aside stops their instructions loading. |
| "I answered rules 1 to 8 from the codebase." | Those are the project's to lock. A guess written there reads as settled to the next session. |
| "I added a gate, so I added a step to the workflow." | The workflow names no gate. `bin/verify` reads the declaration, and a step naming one is the copy that goes stale. |
| "The project has a `gates.yml` already, so CI is covered." | `adopt` reports `present` and writes nothing. Read theirs and say whether it runs `bin/verify`. |
