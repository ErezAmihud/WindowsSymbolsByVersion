"""
Mark a UUID as processed by appending it to process_builds.json.
Replaces the inline python3 -c one-liner in the deploy_manifest CI job.
"""
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("uuid", help="UUID to mark as processed")
    parser.add_argument("--file", default="process_builds.json")
    args = parser.parse_args()

    path = Path(args.file)
    data = json.loads(path.read_text()) if path.exists() else []

    if args.uuid not in data:
        data.append(args.uuid)
        path.write_text(json.dumps(data))
        print(f"Marked {args.uuid} as processed in {args.file}")
    else:
        print(f"{args.uuid} already in {args.file}")

if __name__ == "__main__":
    main()
