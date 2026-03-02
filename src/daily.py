import sys
import json
import argparse
from pathlib import Path

from src.uupdump import get_listid, get_langs

def main():
    parser = argparse.ArgumentParser(description="Get not figured out builds")
    parser.add_argument("allowed_size", type=int, help="Number of builds to output")
    args = parser.parse_args()

    processed_builds = set()
    if Path("process_builds.json").exists():
        with open("process_builds.json", "r") as f:
            processed_builds.update(json.load(f))

    if Path("problematic.json").exists():
        with open("problematic.json", "r") as f:
            processed_builds.update(json.load(f))

    priority_uuids = set()
    if Path("priority.json").exists():
        with open("priority.json", "r") as f:
            priority_uuids.update(json.load(f))

    priority_uuids.difference_update(processed_builds)

    builds = get_listid()

    # Move priority builds to the front
    for uuid in priority_uuids:
        for build in builds:
            if build.uuid == uuid:
                builds.remove(build)
                builds.insert(0, build)
                break

    # Filtering
    builds = filter(lambda b: b.uuid not in processed_builds, builds)
    builds = filter(lambda b: b.arch in ["x86", "amd64"], builds)
    builds = filter(lambda b: "cumulative update" not in b.title.lower(), builds)
    builds = filter(lambda b: " insider " not in b.title.lower(), builds)
    builds = filter(lambda b: " preview " not in b.title.lower(), builds)

    # Note: get_langs is potentially slow so we do it last, on demand.
    # We will compute only up to `allowed_size` matches.
    
    actual_builds = []
    
    for build in builds:
        if "en-us" in get_langs(build.uuid):
            print(build.uuid, str(build))
            actual_builds.append(build.uuid)
            if len(actual_builds) >= args.allowed_size:
                break

    print(actual_builds)
    with open("a.txt", 'w') as f:
        json.dump(actual_builds, f)

if __name__ == "__main__":
    main()
