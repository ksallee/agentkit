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

**A second reader reopens it, and it was reopened.** @salleedesign got write
access on 2026-08-30 and the line was asked again the same hour. The permission
holds for now: somebody who has read nothing is not yet reviewing. It gets
asked a third time at his first review of a pull request, which is the event
this clause was written for.

Settled 2026-08-29 in #6, which carries what the alternative was.

## Who owns what

One row per area, naming who decides when two answers conflict. The areas are
the `area:` labels on the board.

| Area | Owner |
|---|---|
| Rules: `CLAUDE.md`, `WORKFLOW.md`, `STYLE.md` | @ksallee |
| Mechanism: `bin/`, `seeds.json`, the manifest | @ksallee |
| Skills: what a project gets under `.claude/` | @ksallee |

One person owns every area, so no row settles a disagreement today.
@salleedesign has write access and owns none of them. A second owner is one
edit to the table, made when he takes an area rather than when he arrives.

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
