"""The process checks, over synthetic pull requests and a borrowed taxonomy.

Nothing here calls GitHub. `bin/check-process --input` takes the bundle
`--dump` writes, which is the same shape the four `gh api` payloads reduce to,
and `probes/gh_pull_request.py` is what pins that reduction to the real
payloads.

Two things this suite is built to catch. A check that passes because nobody
configured it, which is the failure #10 was filed about. And a checker that
crashes on a taxonomy it was not written against, so `component/` and `size/`
appear below in place of `area:` and `effort:`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECK_PROCESS = ROOT / "bin" / "check-process"

AGENTKIT_CONFIG = """
[labels]
area = "area: "
axes = ["effort: "]

[diff]
forbidden = [".agentkit/local.*"]
"""

# Somebody else's labels, in somebody else's shape. A prefix ending in `/`
# rather than `: `, and an axis that is a size rather than an effort.
BORROWED_CONFIG = """
[labels]
area = "component/"
axes = ["size/"]

[diff]
forbidden = ["*.db", "data/**/*.sqlite"]
"""


def load(path: Path):
    """Import an extensionless executable, which cannot be imported by name."""
    loader = SourceFileLoader(path.name.replace("-", "_"), str(path))
    module = module_from_spec(spec_from_loader(loader.name, loader))
    # Registered before it runs, because `@dataclass` resolves annotations
    # through `sys.modules[cls.__module__]` and a module absent from there
    # raises on 3.14.
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


process = load(CHECK_PROCESS)


def pull(**over) -> dict:
    """A pull request that passes every check, before a test breaks one of it."""
    payload = {
        "number": 21,
        "body": "Closes #10\n\nWhat was verified, and what was not.\n",
        "branch": "10-process-job",
        "labels": ["area: mechanism", "enhancement", "effort: session"],
        "commits": [
            {
                "sha": "1234567890abcdef",
                "message": "No process job here, and the one to copy is welded #10\n\nWhy.\n",
                "parents": 1,
            }
        ],
        "files": ["bin/check-process", "tests/test_process.py"],
        "issues": {"10": ["ksallee"]},
    }
    payload.update(over)
    return payload


def project(tmp_path: Path, config: str | None) -> Path:
    root = tmp_path / "project"
    (root / ".agentkit").mkdir(parents=True, exist_ok=True)
    if config is not None:
        (root / ".agentkit" / "process.toml").write_text(config, encoding="utf-8")
    return root


def run(root: Path, payload: dict, tmp_path: Path) -> subprocess.CompletedProcess:
    saved = tmp_path / "pull.json"
    saved.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(CHECK_PROCESS), "--input", str(saved), "--root", str(root)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def status(output: str, name: str) -> str:
    """The verdict on one check, read off the table `report` prints.

    The table ends at the first detail block, whose lines carry the same words.
    """
    for line in output.splitlines():
        if line.startswith("-----"):
            break
        parts = line.split()
        if len(parts) >= 2 and parts[1] == name:
            return parts[0]
    raise AssertionError(f"No line for {name} in:\n{output}")


class TestTheChecksThatTravel:
    def test_a_pull_request_following_every_rule_passes(self, tmp_path):
        done = run(project(tmp_path, AGENTKIT_CONFIG), pull(), tmp_path)
        assert done.returncode == 0, done.stdout
        assert "none failed" in done.stdout

    def test_a_body_that_closes_nothing_fails(self, tmp_path):
        done = run(project(tmp_path, AGENTKIT_CONFIG), pull(body="A change.\n"), tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "body") == "FAIL"

    def test_a_closes_line_below_the_first_line_fails(self, tmp_path):
        """Rule 16 says the body starts with it, and a reader sees the first line."""
        done = run(project(tmp_path, AGENTKIT_CONFIG), pull(body="Some context.\n\nCloses #10\n"), tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "body") == "FAIL"

    def test_a_branch_naming_another_issue_fails(self, tmp_path):
        done = run(project(tmp_path, AGENTKIT_CONFIG), pull(branch="12-something-else"), tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "branch") == "FAIL"
        assert "#12" in done.stdout

    def test_a_branch_with_no_number_fails(self, tmp_path):
        done = run(project(tmp_path, AGENTKIT_CONFIG), pull(branch="process-job"), tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "branch") == "FAIL"

    def test_a_second_closed_issue_is_a_branch_the_check_accepts(self, tmp_path):
        """Rule 11: one branch may close several issues, named after the main one."""
        payload = pull(body="Closes #10\nCloses #12\n", branch="12-the-other-one", issues={"10": ["a"], "12": ["b"]})
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 0, done.stdout

    def test_an_unassigned_issue_fails(self, tmp_path):
        done = run(project(tmp_path, AGENTKIT_CONFIG), pull(issues={"10": []}), tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "assignee") == "FAIL"

    def test_an_issue_the_fetch_could_not_read_fails_rather_than_passes(self, tmp_path):
        done = run(project(tmp_path, AGENTKIT_CONFIG), pull(issues={}), tmp_path)
        assert done.returncode == 1
        assert "Could not read #10" in done.stdout

    def test_a_subject_with_no_issue_number_fails(self, tmp_path):
        payload = pull(commits=[{"sha": "abc12345", "message": "Add the process job\n", "parents": 1}])
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "subjects") == "FAIL"

    def test_a_type_prefix_fails(self, tmp_path):
        payload = pull(commits=[{"sha": "abc12345", "message": "feat: the process job #10\n", "parents": 1}])
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert "type prefix" in done.stdout

    def test_a_merge_commit_is_exempt(self, tmp_path):
        """Rule 12 says merge `main` in, so the merge commit it produces cannot fail rule 13."""
        payload = pull(
            commits=[
                {"sha": "abc12345", "message": "Merge branch 'main' into 10-process-job\n", "parents": 2},
                {"sha": "def12345", "message": "The subject #10\n", "parents": 1},
            ]
        )
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 0, done.stdout

    def test_a_banned_pattern_in_the_body_fails(self, tmp_path):
        """Rule 24 over the two surfaces bin/check-style never sees.

        The dash is built rather than typed, so this file stays inside the
        style gate it is testing.
        """
        body = "Closes #10\n\nA fix " + chr(8212) + " and its reason.\n"
        done = run(project(tmp_path, AGENTKIT_CONFIG), pull(body=body), tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "style") == "FAIL"
        assert "em dash" in done.stdout

    def test_a_banned_pattern_in_a_subject_fails(self, tmp_path):
        payload = pull(
            commits=[{"sha": "abc12345", "message": "A fix " + chr(8212) + " and its reason #10\n", "parents": 1}]
        )
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "style") == "FAIL"

    def test_the_style_rules_are_the_ones_check_style_holds(self):
        """One list. A second copy is the one that drifts."""
        style = load(ROOT / "bin" / "check-style")
        assert [r[0] for r in process.style_rules()] == [r[0] for r in style.RULES]


class TestTheCaptureWaiver:
    def test_a_capture_change_waives_the_four_checks_that_read_an_issue(self, tmp_path):
        payload = pull(
            body="Capture change, no issue.\n\nWhat was said, and where it landed.\n",
            branch="capture-merge-permission",
            commits=[{"sha": "abc12345", "message": "Record who merges\n", "parents": 1}],
        )
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 0, done.stdout
        for name in ("body", "branch", "assignee", "subjects"):
            assert status(done.stdout, name) == "waived"

    def test_a_capture_change_still_answers_for_its_labels_and_its_diff(self, tmp_path):
        payload = pull(
            body="Capture change, no issue.\n",
            branch="capture-thing",
            commits=[{"sha": "abc12345", "message": "Record it\n", "parents": 1}],
            labels=["enhancement"],
            files=[".agentkit/local.md"],
        )
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "labels") == "FAIL"
        assert status(done.stdout, "diff") == "FAIL"


class TestWhatAProjectConfigures:
    def test_two_area_labels_fail(self, tmp_path):
        payload = pull(labels=["area: rules", "area: mechanism", "bug"])
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "labels") == "FAIL"

    def test_an_effort_label_never_counts_as_the_kind(self, tmp_path):
        payload = pull(labels=["area: mechanism", "effort: quick"])
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert "No kind label" in done.stdout

    def test_a_personal_file_in_the_diff_fails(self, tmp_path):
        payload = pull(files=["bin/check-process", ".agentkit/local.md"])
        done = run(project(tmp_path, AGENTKIT_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "diff") == "FAIL"


class TestAnotherProjectsTaxonomy:
    """The verification #10 asks for: a different taxonomy reports rather than crashes."""

    def test_a_borrowed_taxonomy_passes_on_its_own_labels(self, tmp_path):
        payload = pull(labels=["component/api", "size/small", "bug"])
        done = run(project(tmp_path, BORROWED_CONFIG), payload, tmp_path)
        assert done.returncode == 0, done.stdout
        assert status(done.stdout, "labels") == "pass"

    def test_a_borrowed_taxonomy_reports_its_own_failure(self, tmp_path):
        payload = pull(labels=["component/api", "component/web", "bug"])
        done = run(project(tmp_path, BORROWED_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert "component/" in done.stdout
        assert "Traceback" not in done.stderr

    def test_agentkit_labels_under_a_borrowed_taxonomy_report_rather_than_crash(self, tmp_path):
        """The label set and the config disagree completely, which is the crash case."""
        done = run(project(tmp_path, BORROWED_CONFIG), pull(), tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "labels") == "FAIL"
        assert "Traceback" not in done.stderr

    def test_a_deep_glob_matches_a_captured_file(self, tmp_path):
        payload = pull(files=["data/2026/august/hours.sqlite"])
        done = run(project(tmp_path, BORROWED_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "diff") == "FAIL"

    def test_a_database_anywhere_in_the_tree_matches(self, tmp_path):
        payload = pull(files=["web/src/fixtures/sample.db"])
        done = run(project(tmp_path, BORROWED_CONFIG), payload, tmp_path)
        assert done.returncode == 1
        assert "sample.db" in done.stdout


class TestAProjectWithNoTaxonomy:
    """Question 3. Absent and said so, on every run."""

    def test_the_configured_checks_report_absent_rather_than_pass(self, tmp_path):
        payload = pull(labels=["bug"], files=["anything.db"])
        done = run(project(tmp_path, None), payload, tmp_path)
        assert done.returncode == 0, done.stdout
        assert status(done.stdout, "labels") == "absent"
        assert status(done.stdout, "diff") == "absent"
        assert ".agentkit/process.toml" in done.stdout

    def test_the_five_checks_that_travel_still_fail(self, tmp_path):
        """An unconfigured project is not an unchecked one."""
        done = run(project(tmp_path, None), pull(branch="nothing"), tmp_path)
        assert done.returncode == 1
        assert status(done.stdout, "branch") == "FAIL"

    def test_an_empty_forbidden_list_is_absent_rather_than_a_check_that_cannot_fail(self, tmp_path):
        root = project(tmp_path, '[labels]\narea = "area: "\n\n[diff]\nforbidden = []\n')
        done = run(root, pull(), tmp_path)
        assert done.returncode == 0, done.stdout
        assert status(done.stdout, "diff") == "absent"

    def test_the_absent_line_reaches_the_job_summary(self, tmp_path):
        """A skip nobody can see is the decoration this check exists to avoid."""
        summary = tmp_path / "summary.md"
        saved = tmp_path / "pull.json"
        saved.write_text(json.dumps(pull()), encoding="utf-8")
        done = subprocess.run(
            [sys.executable, str(CHECK_PROCESS), "--input", str(saved), "--root", str(project(tmp_path, None))],
            capture_output=True,
            text=True,
            cwd=ROOT,
            env={**os.environ, "GITHUB_STEP_SUMMARY": str(summary)},
        )
        assert done.returncode == 0, done.stdout
        assert "absent" in summary.read_text(encoding="utf-8")

    def test_a_config_that_is_not_valid_toml_says_so(self, tmp_path):
        root = project(tmp_path, "[labels\narea =\n")
        done = run(root, pull(), tmp_path)
        assert done.returncode != 0
        assert "not valid TOML" in done.stderr + done.stdout


class TestRule12:
    def test_a_fast_forward_push_passes(self, tmp_path):
        repo = git_history(tmp_path)
        before = sha(repo, "HEAD~2")
        after = sha(repo, "HEAD")
        done = push(repo, before, after)
        assert done.returncode == 0, done.stdout

    def test_a_rewritten_history_fails(self, tmp_path):
        repo = git_history(tmp_path)
        before = sha(repo, "HEAD")
        subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=repo, check=True, capture_output=True)
        commit(repo, "A different second commit #10")
        done = push(repo, before, sha(repo, "HEAD"))
        assert done.returncode == 1
        assert "force-push" in done.stdout

    def test_a_created_branch_has_no_history_to_lose(self, tmp_path):
        repo = git_history(tmp_path)
        done = push(repo, "0" * 40, sha(repo, "HEAD"))
        assert done.returncode == 0, done.stdout

    def test_a_sha_the_checkout_never_had_fails_rather_than_raises(self, tmp_path):
        repo = git_history(tmp_path)
        done = push(repo, "a" * 40, sha(repo, "HEAD"))
        assert done.returncode == 1
        assert "Traceback" not in done.stderr


def commit(repo: Path, subject: str) -> None:
    (repo / "file.txt").write_text(subject, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", subject], cwd=repo, check=True, capture_output=True)


def git_history(tmp_path: Path) -> Path:
    repo = tmp_path / "history"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    for n in range(3):
        commit(repo, f"Commit {n} #10")
    return repo


def sha(repo: Path, rev: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", rev], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def push(repo: Path, before: str, after: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECK_PROCESS), "--push", "--before", before, "--after", after, "--root", str(repo)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@pytest.mark.parametrize(
    "branch,expected",
    [("10", 10), ("10-slug", 10), ("10-2-slug", 10), ("main", None), ("v10-slug", None)],
)
def test_a_branch_name_carries_its_issue_number(branch, expected):
    found = process.BRANCH.match(branch)
    assert (int(found.group(1)) if found else None) == expected
