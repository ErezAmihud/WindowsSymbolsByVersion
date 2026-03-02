"""
Merge multiple manifest files, deduplicate lines, and write to an output file.
Replaces the shell 'type | sort | findstr /V' step in CI.
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="Merge and deduplicate manifest files.")
    parser.add_argument("inputs", nargs="+", help="Input manifest files to merge")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    args = parser.parse_args()

    entries: set[str] = set()
    for path in args.inputs:
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.add(line)
        except FileNotFoundError:
            print(f"Warning: {path} not found, skipping.")

    with open(args.output, "w") as out:
        for entry in sorted(entries):
            out.write(entry + "\n")

    print(f"Wrote {len(entries)} unique entries to '{args.output}'")

if __name__ == "__main__":
    main()
