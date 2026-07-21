"""Test for the builds_state.json state machine in code/state.py.

Run from the repo root: python3 tests/test_state.py
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
)
import state as state_mod
from state import MAX_FAILURES, excluded_uuids, mark_done, mark_failed, priority_uuids

STATE_PY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code", "state.py"
)


def test_module():
    state = {"priority": ["prio-1"], "builds": {}}

    # transient failures are retried until MAX_FAILURES
    for i in range(1, MAX_FAILURES + 1):
        mark_failed(state, "flaky-1", run_url=f"https://run/{i}")
        assert state["builds"]["flaky-1"]["failures"] == i
        assert ("flaky-1" in excluded_uuids(state)) == (i >= MAX_FAILURES)

    # success replaces a failed entry and clears priority
    mark_failed(state, "prio-1")
    mark_done(state, "prio-1", "Windows 11, version 24H2 (26100.1)", "26100.1", "amd64")
    assert state["builds"]["prio-1"]["status"] == "done"
    assert "failures" not in state["builds"]["prio-1"]
    assert "prio-1" in excluded_uuids(state)
    assert priority_uuids(state) == set()


def test_cli():
    with tempfile.TemporaryDirectory() as tmp:
        state_file = os.path.join(tmp, "builds_state.json")
        json.dump({"priority": [], "builds": {}}, open(state_file, "w"))

        def run(*args):
            subprocess.run([sys.executable, STATE_PY, *args], check=True, cwd=tmp)

        run("mark-failed", "u-1", "--run-url", "https://example/run/1")
        run("mark-failed", "u-1")
        run(
            "mark-done",
            "u-2",
            "--title",
            "Windows 11 (26100.1)",
            "--build",
            "26100.1",
            "--arch",
            "amd64",
        )

        state = json.load(open(state_file))
        assert state["builds"]["u-1"] == {
            "status": "failed",
            "failures": 2,
            "last_run": None,
        }
        assert state["builds"]["u-2"] == {
            "status": "done",
            "title": "Windows 11 (26100.1)",
            "build": "26100.1",
            "arch": "amd64",
        }


def test_repo_state_consistent():
    """Every manifest on disk must belong to a done build. Done builds may
    lack a manifest (the 2026-07 purge deleted pre-path-data manifests but
    kept their state entries so they are never reprocessed)."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state = json.load(open(os.path.join(repo, "builds_state.json")))
    done = {u for u, i in state["builds"].items() if i["status"] == "done"}
    manifests = {
        f[:-9]
        for f in os.listdir(os.path.join(repo, "manifests"))
        if f.endswith(".manifest")
    }
    assert manifests <= done, f"manifest-without-done={sorted(manifests - done)[:5]}"


if __name__ == "__main__":
    test_module()
    test_cli()
    test_repo_state_consistent()
    print("test_state OK")
