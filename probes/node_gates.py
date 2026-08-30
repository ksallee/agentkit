"""What the seeded node scaffolding does before an install and after one.

    python3 probes/node_gates.py

`bin/adopt` runs `pnpm install` before the gate run for a pack whose gates name
pnpm, and the reason is a claim about pnpm and node that neither this
repository nor a docstring can settle. This copies the three files agentkit
seeds into a throwaway directory and prints what each gate command actually
says, first with no `node_modules` and then with one.

The 2026-08-30 run on pnpm 10.15.0 and Node 22.20.0, which is what #112 was
decided on:

    before install  test   exit 0
    before install  check  exit 1, sh: tsc: command not found
    install         1.6s into an empty store, 0.8s into a warm one
    after install   test   exit 0
    after install   check  exit 0

So `pnpm test` is a gate with nothing installed and `pnpm check` is not. Rerun
this when either version moves.

Standard library only, and it writes nothing outside its own temporary
directory.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The three files `seeds.json` hands a typescript pack. Read from this
# repository rather than written out here, so the probe measures what a project
# receives and cannot drift from it.
SEEDED = ("package.json", "tsconfig.json", "tests/scaffolding.test.mjs")

# The gate list the `typescript` pack declares, minus the style gate, which
# runs a seeded checker and has nothing to do with node.
COMMANDS = ("test", "check")

# One gate on a warm machine takes under a second. Ten times that is a hung
# download rather than a slow one.
TIMEOUT_SECONDS = 120


def stage(where: Path) -> None:
    """Copy the seeded files in, and a gate declaration for the test to read."""
    for rel in SEEDED:
        target = where / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    gates = where / ".agentkit"
    gates.mkdir()
    (gates / "gates.toml").write_text(
        "".join(f'[[gate]]\nname = "{name}"\ncommand = "pnpm {name}"\n\n' for name in COMMANDS)
    )


def run(where: Path, *argv: str) -> tuple[int, str, float]:
    """One command in the staged directory, as (exit code, output, seconds)."""
    started = time.monotonic()
    try:
        done = subprocess.run(
            argv,
            cwd=where,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, f"{type(exc).__name__}: {exc}", time.monotonic() - started
    return done.returncode, (done.stdout + done.stderr).strip(), time.monotonic() - started


def report(label: str, code: int, output: str, seconds: float) -> None:
    print(f"\n{label}  exit {code}  {seconds:.1f}s")
    for line in output.splitlines()[-6:]:
        print(f"    {line}")


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    for tool in ("pnpm", "node"):
        if shutil.which(tool) is None:
            print(f"No {tool} on this machine, so there is nothing to probe.")
            return 0
    print(f"pnpm  {run(Path.cwd(), 'pnpm', '--version')[1]}")
    print(f"node  {run(Path.cwd(), 'node', '--version')[1]}")
    print(f"seeded scripts  {json.loads((ROOT / 'package.json').read_text())['scripts']}")

    with tempfile.TemporaryDirectory() as tmp:
        where = Path(tmp) / "project"
        where.mkdir()
        stage(where)

        for name in COMMANDS:
            report(f"before install  {name}", *run(where, "pnpm", name))

        # An empty store, so the number is the worst case a first adoption
        # pays. A machine that has installed typescript before is faster.
        store = Path(tmp) / "store"
        report("install", *run(where, "pnpm", "install", "--store-dir", str(store)))

        for name in COMMANDS:
            report(f"after install   {name}", *run(where, "pnpm", name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
