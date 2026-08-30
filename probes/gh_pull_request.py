#!/usr/bin/env python3
"""Print what `gh api` returns for the four calls the process job reads.

    python3 probes/gh_pull_request.py --repo ksallee/agentkit --pull 18

Rule 9. `bin/check-process` asserts rules 11, 13, 15, 16 and 19 over a pull
request, and every field it reads comes from one of these payloads.

Two shapes cost a run to discover and both change what the checker can do:

- `gh pr view --json commits` truncates `messageHeadline` at 72 characters
  with an ellipsis, and carries no parent list. Rule 13 is a check on the end
  of a subject, and it exempts merge commits, so that call serves neither.
  `pulls/{n}/commits` carries `commit.message` whole and `parents`.
- An issue's assignees are a list of objects. `[]` is the unassigned case rule
  11 fails on, and it is what an issue nobody claimed returns.

Prints. Writes nothing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def call(path: str, paginate: bool = False) -> object:
    args = ["gh", "api", path] + (["--paginate"] if paginate else [])
    done = subprocess.run(args, capture_output=True, text=True)
    if done.returncode != 0:
        print(f"  {' '.join(args)} exited {done.returncode}: {done.stderr.strip()[:200]}")
        return None
    return json.loads(done.stdout)


def show(title: str, payload: object, fields: tuple[str, ...]) -> None:
    print(f"\n{title}")
    if payload is None:
        return
    rows = payload if isinstance(payload, list) else [payload]
    print(f"  {len(rows)} row(s)")
    for row in rows[:3]:
        print(f"  keys: {sorted(row)}")
        for field in fields:
            value: object = row
            for part in field.split("."):
                value = value.get(part) if isinstance(value, dict) else None
            print(f"    {field} = {json.dumps(value)[:180]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe the payloads bin/check-process reads.")
    ap.add_argument("--repo", default="ksallee/agentkit")
    ap.add_argument("--pull", type=int, default=18)
    ap.add_argument("--issue", type=int, default=17)
    args = ap.parse_args()

    base = f"repos/{args.repo}"
    show(
        f"{base}/pulls/{args.pull}",
        call(f"{base}/pulls/{args.pull}"),
        ("number", "body", "head.ref", "labels", "draft"),
    )
    show(
        f"{base}/pulls/{args.pull}/commits",
        call(f"{base}/pulls/{args.pull}/commits", paginate=True),
        ("sha", "commit.message", "parents"),
    )
    show(
        f"{base}/pulls/{args.pull}/files",
        call(f"{base}/pulls/{args.pull}/files", paginate=True),
        ("filename", "status", "previous_filename"),
    )
    show(
        f"{base}/issues/{args.issue}",
        call(f"{base}/issues/{args.issue}"),
        ("number", "assignees", "state"),
    )

    print("\nThe call the checker never makes, and why:")
    done = subprocess.run(
        ["gh", "pr", "view", str(args.pull), "--repo", args.repo, "--json", "commits"],
        capture_output=True,
        text=True,
    )
    if done.returncode == 0:
        for commit in json.loads(done.stdout)["commits"]:
            print(f"  messageHeadline = {json.dumps(commit['messageHeadline'])}")
            print(f"  parents         = {json.dumps(commit.get('parents'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
