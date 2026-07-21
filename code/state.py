#!/usr/bin/env python3
"""Owns builds_state.json - the single record of what happened to every build.

Schema:
{
  "priority": ["<uuid>", ...],          # user-requested builds, picked first
  "builds": {
    "<uuid>": {"status": "done", "title": "...", "build": "...", "arch": "..."}
    "<uuid>": {"status": "failed", "failures": 2, "last_run": "<run url>"}
  }
}

A build is excluded from further processing once it is done, or once it failed
MAX_FAILURES times (transient runner/uupdump errors get retried until then).

CLI used by the workflows:
  state.py mark-done <uuid> [--title T --build B --arch A]   (looked up on uupdump if omitted)
  state.py mark-failed <uuid> [--run-url URL]
"""

import argparse
import json

STATE_FILE = "builds_state.json"
MAX_FAILURES = 3


def load_state(path=STATE_FILE):
    return json.load(open(path))


def save_state(state, path=STATE_FILE):
    state["priority"] = sorted(set(state["priority"]))
    state["builds"] = dict(sorted(state["builds"].items()))
    with open(path, "w") as f:
        json.dump(state, f, indent=1)
        f.write("\n")


def excluded_uuids(state):
    """Uuids that must not be attempted again."""
    return {
        uuid
        for uuid, info in state["builds"].items()
        if info["status"] == "done" or info.get("failures", 0) >= MAX_FAILURES
    }


def priority_uuids(state):
    return set(state["priority"])


def mark_done(state, uuid, title, build, arch):
    state["builds"][uuid] = {
        "status": "done",
        "title": title,
        "build": build,
        "arch": arch,
    }
    if uuid in state["priority"]:
        state["priority"].remove(uuid)


def mark_failed(state, uuid, run_url=None):
    info = state["builds"].get(uuid, {})
    failures = info.get("failures", 0) + 1 if info.get("status") == "failed" else 1
    state["builds"][uuid] = {
        "status": "failed",
        "failures": failures,
        "last_run": run_url,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    done = sub.add_parser("mark-done")
    done.add_argument("uuid")
    done.add_argument("--title")
    done.add_argument("--build")
    done.add_argument("--arch")
    failed = sub.add_parser("mark-failed")
    failed.add_argument("uuid")
    failed.add_argument("--run-url")
    args = parser.parse_args()

    state = load_state()
    if args.command == "mark-done":
        title, build, arch = args.title, args.build, args.arch
        if title is None:
            from uupdump import listid  # only the network-using path needs deps

            matches = [b for b in listid() if b.uuid == args.uuid]
            if matches:
                title, build, arch = matches[0].title, matches[0].build, matches[0].arch
            else:
                # delisted from uupdump between pick and deploy - keep the manifest anyway
                title, build, arch = f"Unknown build {args.uuid}", "", ""
        mark_done(state, args.uuid, title, build or "", arch or "")
    else:
        mark_failed(state, args.uuid, args.run_url)
    save_state(state)


if __name__ == "__main__":
    main()
