---
name: adopt
description: Seed the agentkit scaffolding into a project, or update a project that already has it. Asks the five answers the team layer needs, shows the plan, and writes only after somebody has read it. Use when someone says "adopt agentkit here", "set this project up", "update the scaffolding", or asks what a rerun would change.
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

## The five answers

Ask all five in one pass. Four carry a default worth accepting.

| Answer | Flag | Default |
|---|---|---|
| Which gates the project runs | `--pack python\|typescript\|python+typescript\|none` | **None. This is the one it will not guess.** |
| The project's name | `--name` | The directory name. |
| One line saying what it is | `--summary` | Left unanswered in `team.md`, marked as such. |
| Who reviews and who merges | `--merge` | The author does not merge their own pull request. |
| Shaping or building | `--phase` | `building` when the target has a commit, `shaping` when it does not. |

**The pack has no default and adopt refuses to write the team layer without
it.** A gate list naming a command the project does not run makes rule 17
disagree with CI, and a rule CI contradicts is worse than an absent one.
Guessing `python` from a `pyproject.toml` gets every project with a `web/` half
wrong. Ask.

The seeded gate list is a starting point that nothing verified. After the
write, run each command in `.agentkit/gates.toml` once and correct the file
where one fails for the wrong reason.

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
git add .agentkit docs .claude && git commit
```

The manifest is committed, so both people see the same adoption state.

## Updating later

The same command. A file nobody touched comes back `unchanged` or `updated`,
and a file somebody edited comes back `kept` with both names on the line. The
team layer is seeded once and never rewritten, so an edit to `gates.toml`
survives every rerun.

## Excuses

| Excuse | Reality |
|---|---|
| "The plan looked fine, I ran the write in the same turn." | Nobody read it. The plan exists to be read back by a person who can say no. |
| "I picked the pack from the lockfiles." | A wrong gate list makes CI and rule 17 disagree, which is the one failure this refuses to risk. |
| "I copied the file across and added the hash myself." | The manifest is the record of what the script wrote. A hand-written row makes the next `kept` a lie. |
| "The sidecar is there, so nothing was lost." | A `.local` file is loaded by nothing. Until somebody merges it, the project lost the file it was using. |
| "It only reported `kept`, so the run did nothing." | `kept` replaces the file. It is the loudest outcome, and it is why the plan is the default. |
