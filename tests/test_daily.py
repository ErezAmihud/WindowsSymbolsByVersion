"""Unit test for the build-picking logic in code/daily.py.

Run from the repo root: python3 tests/test_daily.py
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
)
from daily import pick_builds
from uupdump import BuildInfo


def build(uuid, title="Windows 11, version 24H2 (26100.1)", arch="amd64"):
    return BuildInfo(title=title, build="26100.1", arch=arch, created=1, uuid=uuid)


def main():
    builds = [
        build("done-1"),  # already processed
        build("bad-1"),  # known problematic (also in processed set)
        build("arm-1", arch="arm64"),  # wrong arch
        build("cum-1", title="Cumulative Update for Windows 11 (26100.2)"),
        build("ins-1", title="Windows 11 Insider Preview 10.0.26200.1 (ge_release)"),
        build("pre-1", title="Windows Server Preview build (26080.1)"),
        build("pre-2", title="Preview Update for Windows 11 (28000.2340)"),
        build("new-1"),
        build("new-2"),
        build("nolang-1"),  # not available in en-us
        build("langfail-1"),  # listlangs endpoint keeps failing
        build("new-3"),
        build("prio-1"),  # user-requested priority build
    ]
    processed = {"done-1", "bad-1"}
    priority = {
        "prio-1",
        "done-1",
    }  # priority on a processed build must not resurrect it

    def fake_get_langs(uuid):
        if uuid == "nolang-1":
            return ["de-de"]
        if uuid == "langfail-1":
            raise RuntimeError("api down")
        return ["en-us", "de-de"]

    picked = pick_builds(builds, processed, priority, allowed_size=3, get_langs=fake_get_langs)
    got = [b.uuid for b in picked]
    # priority build first, then list order, skipping everything filtered
    assert got == ["prio-1", "new-1", "new-2"], f"unexpected picks: {got}"

    picked = pick_builds(builds, processed, priority, allowed_size=100, get_langs=fake_get_langs)
    got = [b.uuid for b in picked]
    assert got == ["prio-1", "new-1", "new-2", "new-3"], f"unexpected picks: {got}"

    picked = pick_builds(
        builds,
        processed | {"prio-1", "new-1", "new-2", "new-3"},
        priority,
        100,
        fake_get_langs,
    )
    assert picked == [], f"expected no picks, got: {[b.uuid for b in picked]}"

    print("test_daily OK")


if __name__ == "__main__":
    main()
