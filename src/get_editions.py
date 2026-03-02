"""Get editions for a UUPDump UUID and print in GitHub Actions output format."""
import argparse
import os
from src.uupdump import get_editions

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("uuid")
    parser.add_argument("--lang", default="en-us")
    args = parser.parse_args()

    editions = get_editions(args.uuid, args.lang)
    output = "editions=" + ";".join(editions)
    print(output)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(output + "\n")

if __name__ == "__main__":
    main()
