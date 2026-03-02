"""
Mark a UUID as problematic by appending it to problematic.json.
Replaces the inline python3 -c one-liner in the failed-create-iso CI job.
"""
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("uuid", help="UUID to mark as problematic")
    parser.add_argument("--file", default="problematic.json")
    args = parser.parse_args()

    path = Path(args.file)
    data = json.loads(path.read_text()) if path.exists() else []

    if args.uuid not in data:
        data.append(args.uuid)
        path.write_text(json.dumps(data))
        print(f"Marked {args.uuid} as problematic in {args.file}")
    else:
        print(f"{args.uuid} already in {args.file}")

if __name__ == "__main__":
    main()
