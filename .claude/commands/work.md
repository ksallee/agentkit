---
description: What is worth doing next, from the open issues
---
Run the `pick-work` skill in `.claude/skills/pick-work/`.

`adopt` seeds every project a command named after the project, and that is
where a session starts: it reads the three layers and `.agentkit/phase.json`,
then says where the last session stopped. This one reads the board, and the
entry point hands over to it.

Show me open pull requests first, then group the open issues by what each needs
in order to be verified, using this project's own `effort:` labels and their
descriptions. Tell me what is blocked and on what. Propose three or four, say
what each would touch, and wait for me to choose. Do not start anything or
spawn agents without a yes.
