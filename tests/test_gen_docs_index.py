"""Unit test for the "available" badge count in code/gen_docs_index.py.

Run from the repo root: pytest tests/test_gen_docs_index.py
"""

from unittest.mock import patch

from gen_docs_index import count_available
from uupdump import AvailableArchTypes, BuildInfo


def build(
    uuid,
    title="Windows 11, version 24H2 (26100.1)",
    arch: AvailableArchTypes = "amd64",
):
    return BuildInfo(title=title, build="26100.1", arch=arch, created=1, uuid=uuid)


def test_count_available_matches_pipeline_scope():
    builds = [
        build("new-1"),
        build("new-2"),
        build("arm-1", arch="arm64"),  # wrong arch
        build("cum-1", title="Cumulative Update for Windows 11 (26100.2)"),
        build("ins-1", title="Windows 11 Insider Preview 10.0.26200.1 (ge_release)"),
        build("pre-1", title="Windows Server Preview build (26080.1)"),
    ]
    with patch("gen_docs_index.listid", return_value=builds):
        assert count_available() == 2
