# agentkit

The scaffolding a project adopts: the rules, the skills, the role guides and
the design pipeline.

## The layer this file is

Committed, and it wins over anybody's `.agentkit/local.md` on anything two
people have to agree on. One person opting out of the gate list is a decision
two people make.

## Who reviews and who merges

The agent merges the pull requests it opens. Two conditions come with that:

- **The gates pass first.** `bin/verify` prints a table, and that table goes in
  the pull request body. Rule 17: a gate reported green without its output in
  the session did not pass.
- **The operator QAs after the fact.** A defect found then is a new issue, and
  the branch that would have waited for a review is already off the board.

**A second reader reopens it. It was reopened and it held.** @salleedesign got
write access on 2026-08-30 and the line was asked the same hour. He adopts this
scaffolding into his own projects and does not work on it, so agentkit has one
operator and the clause describes a situation that has not arrived. It gets
asked again at his first review of a pull request here.

Settled 2026-08-29 in #6, which carries what the alternative was.

## Who owns what

One row per area, naming who decides when two answers conflict. The areas are
the `area:` labels on the board.

| Area | Owner |
|---|---|
| Rules: `CLAUDE.md`, `WORKFLOW.md`, `STYLE.md` | @ksallee |
| Mechanism: `bin/`, `seeds.json`, the manifest | @ksallee |
| Skills: what a project gets under `.claude/` | @ksallee |

One person owns every area, so no row settles a disagreement today. A second
owner is one edit to the table, made when somebody takes an area rather than
when they arrive.

**@salleedesign adopts this, he does not maintain it.** Write access, no area,
and the first person to run `bin/adopt` against a project whose rules nobody
here wrote. That makes him the audience for `templates/`, the role guides and
everything under `.claude/skills/`, and the reason a question about what a
seeded project gets outranks a question about what this repository has. #25 is
where that run is tracked, and it stopped being hypothetical on 2026-08-30.

## Conventions this project settled

**A commit carries two attribution trailers.** Rule 13 sends the question here,
and nothing in the rules depends on the answer.

```
Claude-Session: https://claude.ai/code/session_<id>
Co-authored-by: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

The agent writes both, and a commit made by hand carries neither. The session
line is the one path from a merged commit back to the conversation behind it
once the pull request has scrolled away. No gate checks either line.
