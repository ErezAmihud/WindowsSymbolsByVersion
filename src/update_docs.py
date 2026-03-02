"""
Append a docs link entry for a build to docs/index.md.
Replaces the inline echo -e step in the deploy_manifest CI job.
"""
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("build_name", help="Human-readable build name")
    parser.add_argument("uuid", help="UUID of the build")
    parser.add_argument("--docs-file", default="docs/index.md")
    parser.add_argument(
        "--repo",
        default="ErezAmihud/WindowsSymbolsByVersion",
        help="GitHub repo path (user/repo)"
    )
    args = parser.parse_args()

    url = f"https://github.com/{args.repo}/blob/main/manifests/{args.uuid}.manifest"
    line = f"[{args.build_name}]({url})\n\n"

    with open(args.docs_file, "a") as f:
        f.write(line)
    print(f"Appended '{args.build_name}' to {args.docs_file}")

if __name__ == "__main__":
    main()
