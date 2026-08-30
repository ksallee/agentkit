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

Say back two things. They ride in the message that carries the first
`AskUserQuestion` call, as a statement the operator corrects rather than a gate
they clear first. Waiting for a separate yes costs a round trip and buys
nothing, because nothing is written until the plan is approved:

- **The directory**, as an absolute path. "Here" is the session's working
  directory, and a session started somewhere else adopts somewhere else.
- **First adoption or update**, and what said so. `.agentkit/manifest.json`
  present means the project was adopted before and this run replaces seeded
  files. Absent means nothing here has been seeded.

`bin/adopt` reads the manifest for itself, so a misreading costs what the
session does around the tool. A first adoption needs all five answers before
anything is written. An update has them in `.agentkit/team.md` already, and
what it needs read back is which files a rerun replaces and which it keeps. The
wrong directory means every one of those questions was asked about the wrong
project.

## Preconditions

Check these and print the fix. Don't work around them.

| Needs | Check | Fix |
|---|---|---|
| An agentkit checkout, with the session running inside it | `ls bin/adopt` | `git clone git@github.com:ksallee/agentkit.git`, then work from that directory |
| python3 | `python3 --version` | Ships with macOS. |
| The target directory exists | `ls -d <project>` | `git clone <remote> <path>` where the project already has a remote, `mkdir <path>` where it has none |
| The target is a git repository | `git -C <project> rev-parse --git-dir` | `git init` |
| It has a commit, or the operator knows what a write costs without one | `git -C <project> rev-parse HEAD` | Say which of the two states the target is in before writing |

**A new project with an empty remote and no local directory is cloned, never
created by hand.** `git clone <remote> <path>` brings `origin` and the server's
default branch name with it. `git init` takes whatever `init.defaultBranch`
says on that machine, so a local `master` pushed to a remote whose default is
`main` is a two-branch repository, found at the first push. `adopt` performs no
clone, and the directory has to be there before it runs: `git -C` on a path
that does not exist fails with `cannot change to '<path>': No such file or
directory`, a different failure from a directory that is not a repository.

The last two rows are one precondition read twice, and the second carries the
reason. Adoption replaces files and `git checkout` is the way back, so a
repository with a commit has a recovery. A repository with none passes
`rev-parse --git-dir` and has nothing to check out: undoing a write there means
deleting the paths `adopt` printed. That recovers everything only while the
directory was empty. Say which state the target is in, and where it has files and no commits,
say what is in the tree before writing over it. `--phase` reads the same fact
and defaults to `shaping` when there is no commit.

## The five answers

Four carry a default worth accepting.

**Every question carries its options and a recommendation.** That is the
property, and it is the one that failed in #128: four rounds there were spent
on questions the operator could not answer without going to read a skill first.
Round count was the symptom. A question naming its legal values and saying
which one you would take costs the operator one word back.

**Use `AskUserQuestion`, batched.** Stated 2026-08-30: "what I'd like is to use
claude question system, with all questions in one go, that would be the
simplest." It renders each question with its options as choices, so the options
are in front of the operator instead of in a paragraph they have to read back.

**It takes four questions per call, so the set is two calls.** Put the four
with a fixed range in the first: the pack, who merges, shaping or building, and
`surface`. Each option carries what it costs in its `description`, and the one
you would take goes first, labelled `(Recommended)`. The second call takes the
name and the summary, which are free text: give the default as the first option
and let the operator type over it, since `AskUserQuestion` always offers
`Other`.

Asking in bulk is not what went wrong in #128, and batching does not bring it
back. What brings it back is a question with no options in it.

| Answer | Flag | Default |
|---|---|---|
| Which gates the project runs, what CI installs, and which design driver arrives | `--pack python\|typescript\|python+typescript\|none` | **None. This is the one it will not guess.** |
| The project's name | `--name` | The directory name. It also names the project's own slash command. |
| One line saying what it is | `--summary` | Left unanswered in `team.md` and in `CLAUDE.md`, marked as such. |
| Who reviews and who merges | `--merge` | The author does not merge their own pull request. |
| Shaping or building | `--phase` | `building` when the target has a commit, `shaping` when it does not. |

**The pack has no default and adopt refuses to write the team layer without
it.** A gate list naming a command the project does not run makes rule 17
disagree with CI, and a rule CI contradicts is worse than an absent one.
Guessing `python` from a `pyproject.toml` gets every project with a `web/` half
wrong. Ask.

**The pack also selects the design pipeline's browser driver.** The python
packs receive `design/capture.py` and `design/build.py`, `typescript` receives
`design/capture.mjs` and `design/build.mjs`, and `none` receives both pairs.
Every pack receives `design/capture.js`, the contract the drivers share, and
`design/screens.json`.

**`none` is the pack for a project whose toolchain is neither python nor
node.** A Go, Rust, Elixir or plain-HTML project takes it and gets a gate list
that runs on day one: style and probes, the two gates that name no language
toolchain. It gets both capture drivers, and `design-process` step 6 runs
whichever runtime the machine has. What it gets no gate over is the project's
own code, and that is the sentence to say whenever `none` is on the table.

**A first write ends by running the gate list it seeded.** `bin/adopt` invokes
the project's own `bin/verify` and prints its table, so the operator learns on
day one whether the scaffolding holds together. Four things come with that run:

- A red gate leaves `bin/adopt` at 0. The files are written and the manifest
  records them whatever the gates say, and an exit code saying otherwise would
  read as a failed write.
- A machine missing a tool the pack names is told which one, and no gate runs.
  `uvx ruff` on a machine without uv fails under a gate name and says nothing
  about the machine, and a first adoption is where a reader has least basis for
  telling the two apart. `pnpm` is checked the same way for the two packs that
  name it.
- **A pack whose gates run pnpm installs first**, in every directory a gate
  declares: the root for `typescript`, `web/` for `python+typescript`. The
  `check` gate runs `tsc`, which resolves from `node_modules/.bin`, so without
  the install it reports a missing binary and nothing about the project. It
  added 0.8s to an adoption on a machine that had installed typescript before
  and 1.6s into an empty pnpm store, measured 2026-08-30 on #112 by
  `probes/node_gates.py`. A failed install is printed and the gates run anyway.
- A rerun runs nothing, and `--no-gates` skips the install with the run.

The seeded gate list is still a starting point. Correct `.agentkit/gates.toml`
where a gate fails for the wrong reason. The seeded workflow runs the same
command, so a gate that passes here passes there.

The pack also picks what CI installs: uv for every pack, plus node, pnpm and an
install step for a pack with pnpm gates. A gate added later that needs another
tool needs a step in `.github/workflows/gates.yml`.

**`--merge` has a range, and the default is one of three.** Rule 18 lists them:
everything waits for a review, an agent may merge on green, or some class of
change may. Whatever the operator answers goes into `team.md` in their own
words, and no check reads it, because `bin/check-process` cannot tell an
approved merge from an impatient one. An answer other than the default is a
setting the rules offer rather than an exception to them.

The name and the summary reach two files: `.agentkit/team.md` and the project's
`CLAUDE.md`, which an agent loads every turn. A summary nobody gave leaves both
saying so.

### The one design setting

`surface` says where a finished design lands
(`canvas`, `file` or `none`). `adopt` seeds it unanswered, so somebody picks
one before the design skills run. Report it with its three values every time it
comes up. A setting named as unanswered without its options tells the reader to
go and find them in `design-process` step 8, and it was reported that way four
times in one adoption before anybody said what they were.

## Run the plan first, always

```sh
python3 bin/adopt /path/to/project --pack <the answer>
```

Run it from the agentkit checkout, with the target as the path. That writes
nothing. Read the outcome for every file back to the operator
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
`absent` in the run summary until somebody writes it.

**Never offer to write `process.toml` from `gh label list`.** A repository
created for a first adoption carries GitHub's ten stock labels, every one of
them a kind under rule 15 and none of them an area, so a taxonomy generated
from that list declares an area prefix matching nothing and rule 15 fails every
pull request. Two cold runs reported it independently (#125). The file waits
for areas that exist.

## The three `effort:` labels a first write creates

`adopt` creates `effort: quick`, `effort: session` and `effort: blocked` on the
project's own remote, with the descriptions this scaffolding uses, and creates
no `area:` label. Effort says what it costs to verify something and reads the
same in any project. Areas name one project's own parts, and `shape` is what
settles them, so a seeded area taxonomy would be somebody else's labels in a
place that reads as decided.

Four things come with it, and all four go in the report:

- **A first write only.** A rerun reads no label and writes none.
- **It reaches the network, and a failure costs the adoption nothing.** No git
  remote, no `gh` and an unauthenticated `gh` are each named on one line, and
  the files are written either way. `--no-labels` skips it.
- **A label already on the board comes back `present`.** The existing names are
  read before anything is created, so a rerun on a project that has them errors
  on none.
- **The areas are still missing.** Rules 15 and 16 want an `area:` label plus a
  kind on every issue and pull request, and this narrows that gap rather than
  closing it. Say so, name `shape` as where the areas come from, and name the
  directory it runs in: `gh` reads the working directory's remote, so `shape`
  run from the agentkit checkout files against `ksallee/agentkit` (#128).

## The project gets a command named after itself

`adopt` renders one more file: `.claude/commands/<project>.md`, the entry point
a session starts at. It reads the three layers rule 0 names and
`.agentkit/phase.json`, then says where the last session stopped.

| Question | Answer |
|---|---|
| What it does against `/work` | The project's command is the entry point and hands over. `/work` reads the board. Both files say which is which |
| What it does in `shaping` | Names `shape` as the next move. A project in that phase has no board, and `pick-work` already says an empty board is no backlog |
| Where the name comes from | The project name, lowercased, with every run of other characters becoming one hyphen: `CSS Fun Experiments` seeds `/css-fun-experiments`. A name that survives none of that falls back to the directory name |
| Where it lives | Rendered per project like `CLAUDE.md` and the two workflows, so it carries no manifest row, and a rerun leaves an edited copy exactly as it found it |

A name that slugifies to a command `seeds.json` already seeds, `work` or
`done`, is refused and the report says why. That file is a byte copy replaced
on every rerun, so a rendered command written there would be overwritten and
the project would lose its entry point without being told.

## The router is seeded once and replaced never

`CLAUDE.md`, the three `.agentkit/` files, the two workflows and the command
named after the project are rendered from the answers rather than copied, so
they carry no manifest row and no rerun touches them. A workflow this template replaced would leave the project's
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
python3 bin/adopt /path/to/project --write --pack python \
  --name mac-hours --summary "Project-scoped time tracker."
```

Then, in the project:

```sh
git status --short
git add CLAUDE.md .gitignore .agentkit .claude .github bin design docs probes
git add ruff.toml tests/test_scaffolding.py                 # a python pack
git add package.json tsconfig.json pnpm-lock.yaml tests/scaffolding.test.mjs
git commit
```

The manifest is committed, so both people see the same adoption state. The
paths are named one by one because the gate run leaves whatever the gates
cache: in a python project `__pycache__/`, `.pytest_cache/` and `.ruff_cache/`,
and the ignores for those three are the project's own to write. The third line
is the `typescript` pack's, and `python+typescript` takes the same four under
`web/`, where its pnpm gates run. `pnpm-lock.yaml` is committed because CI
installs from it; `node_modules/` is in the ignore block. `probes` is on the
first line because `seeds.json` lists `probes/skill_sources.py` under `tracked`
and every pack receives it. On the python line it goes untracked under
`typescript`, and the manifest records it as written either way, so the next
run reports it `unchanged` and never notices it is missing from git.
`.gitignore` is on the same line for the same reason: `adopt` writes the block
on every run, it carries `.agentkit/local.*`, and rule 19's forbidden list
names that path because an ignore is a default somebody overrides.

**The first commit cannot follow rules 10 to 13, and that is expected.** Rule
11 branches off `origin/main`, absent when this is the repository's first
commit, and rule 10 wants an issue on a board the adoption makes usable. Commit straight to `main`. Rules 11, 13 and 16 are
asserted by `bin/check-process` over a pull request, and a bootstrap commit has
none. Where the project already has history the adoption is ordinary work, and
it takes an issue and a branch like anything else.

## Reporting the run back

**Where the project stands, then what is left, and stop.** Two short paragraphs
and a list. An adoption report is read once, by somebody deciding whether they
can start working, and a wall of detail buries the two lines they needed. Put
anything longer in an issue and name it in the list.

Three things it gets wrong by default. All three were paid for in #109's phase
A, where the operator had to ask four times for something the report should
have carried.

**Name a setting's values whenever the setting is named.** `surface` above is
the standing case, and the pack is the same shape.

**Name the directory every next step runs in.** `shape` runs in the project.
Run it from the agentkit checkout and it files the project's constraint
questions against `ksallee/agentkit`, because `gh` reads the working directory's
remote.

**A finding carries a recommendation, or says why it has none.** A list of gaps
with no proposal against each one moves the deciding back onto whoever asked
for the setup, at the moment they have least context on it.

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
| "The repository had no labels, so I wrote `process.toml` from `gh label list`." | GitHub's ten defaults are every one of them a kind. The area prefix that generates matches nothing, and rule 15 then fails every pull request. |
| "The label call failed, so I stopped." | The files are written whatever GitHub answers. Report the line and carry on. |
| "`/work` exists, so the project-named command is a duplicate." | One starts a session, the other reads the board. Both files say which, and the report names the entry point. |
