"""Minimal helper for talking to the GitHub Actions runner."""

import os
import sys


def write_output(key: str, value: str):
    """Set a step output; echoes to stderr (and stdout when run locally)."""
    print(f"{key}={value}", file=sys.stderr)
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{key}={value}\n")
    else:
        print(f"{key}={value}")
