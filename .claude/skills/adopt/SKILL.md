---
name: adopt
description: Seed the agentkit scaffolding into a project, or update a project that already has it. Asks the six answers the team layer and the router need, shows the plan, and writes only after somebody has read it. Use when someone says "adopt agentkit here", "set this project up", "update the scaffolding", or asks what a rerun would change.
---

# Adopting the scaffolding

`bin/adopt` owns the copying and the hashing. This skill owns the questions.
Never write `.agentkit/manifest.json` by hand, and never copy a seeded file
with `cp`. An improvised manifest lies on the next update.

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
| Which gates the project runs | `--pack python\|typescript\|python+typescript\|none` | **None. This is the one it will not guess.** |
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
write, run each command in `.agentkit/gates.toml` once and correct the file
where one fails for the wrong reason.

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

## The router is seeded once and replaced never

`CLAUDE.md` and the three `.agentkit/` files are rendered from the answers
rather than copied, so they carry no manifest row and no rerun touches them.
Two outcomes, and neither writes over anything:

| Outcome | What it means |
|---|---|
| `seeded` | Nothing was there. `adopt` wrote it from the answers |
| `present` | A file is there. `adopt` left it exactly as it found it |

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
git add CLAUDE.md .agentkit docs .claude && git commit
```

The manifest is committed, so both people see the same adoption state.

## Updating later

The same command. A file nobody touched comes back `unchanged` or `updated`,
and a file somebody edited comes back `kept` with both names on the line. The
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
| "Their `CLAUDE.md` was thin, so I moved it aside." | Four options, and the operator picks. Moving theirs aside stops their instructions loading. |
| "I answered rules 1 to 8 from the codebase." | Those are the project's to lock. A guess written there reads as settled to the next session. |
