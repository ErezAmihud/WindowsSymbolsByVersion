"""
Look up a UUID in the UUPDump build list and print it in GitHub Actions output format.
Replaces the inline python3 -c block in the get_name CI step.
"""
import argparse
import os
import sys
from src.uupdump import get_listid

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("uuid", help="UUID to look up")
    args = parser.parse_args()

    builds = get_listid()
    match = next((b for b in builds if b.uuid == args.uuid), None)
    if match is None:
        print(f"ERROR: UUID '{args.uuid}' not found in UUPDump list.", file=sys.stderr)
        sys.exit(1)

    output = f"name={match}"
    print(output)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(output + "\n")

if __name__ == "__main__":
    main()
