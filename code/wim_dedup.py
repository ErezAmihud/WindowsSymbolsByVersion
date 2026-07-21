#!/usr/bin/env python3
"""List the files worth parsing in every image of a WIM, without extracting anything.

Emits one listfile per image (listfile_<name>_<i>.txt, consumable by
`wimextract @listfile`) containing only files that can contribute a pdb entry:
 - PE-like extensions (plus extensionless files, e.g. bootmgr),
 - whose content hash was not already listed in an earlier image of the same WIM.

Editions inside an install.wim share the vast majority of their files, so this
cuts extraction and parsing work by roughly the number of images.

Prints `version_matrix=[...]` (the image indices that have anything to parse)
to stdout, for $GITHUB_OUTPUT. Diagnostics go to stderr.

Usage: wim_dedup.py <wim_file> <name>
"""

import re
import subprocess
import sys

PE_EXTENSIONS = {
    "acm",
    "ax",
    "com",
    "cpl",
    "dll",
    "drv",
    "efi",
    "exe",
    "ime",
    "msstyles",
    "mui",
    "node",
    "ocx",
    "scr",
    "sys",
    "tsp",
    "winmd",
}
EMPTY_HASH = "0" * 40


def image_count(wim_file):
    out = subprocess.run(
        ["wimlib-imagex", "info", wim_file], check=True, capture_output=True, text=True
    ).stdout
    m = re.search(r"Image Count:\s*(\d+)", out)
    if m is None:
        raise ValueError(f"could not find image count in wimlib-imagex info for {wim_file}")
    return int(m.group(1))


def is_interesting(path):
    name = path.rsplit("/", 1)[-1]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return ext == "" or ext in PE_EXTENSIONS


def list_image_files(wim_file, image):
    """Yield (path, hash) for every regular file in the image."""
    proc = subprocess.Popen(
        ["wimlib-imagex", "dir", wim_file, str(image), "--detailed"],
        stdout=subprocess.PIPE,
        text=True,
        errors="replace",
    )
    path, is_dir, in_unnamed_stream, file_hash = None, False, False, None
    assert proc.stdout is not None  # stdout=PIPE guarantees this
    with proc.stdout:
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("Full Path"):
                if path is not None and not is_dir and file_hash is not None:
                    yield path, file_hash
                path = line.split("=", 1)[1].strip().strip('"')
                is_dir, in_unnamed_stream, file_hash = False, False, None
            elif line == "FILE_ATTRIBUTE_DIRECTORY is set":
                is_dir = True
            elif line.endswith("Unnamed data stream:"):
                in_unnamed_stream = True
            elif line.startswith("Hash") and in_unnamed_stream and file_hash is None:
                file_hash = line.split("=", 1)[1].strip().removeprefix("0x")
    if path is not None and not is_dir and file_hash is not None:
        yield path, file_hash
    if proc.wait() != 0:
        raise subprocess.CalledProcessError(proc.returncode, proc.args)


def main():
    wim_file, name = sys.argv[1], sys.argv[2]
    seen_hashes = set()
    images_with_files = []
    for image in range(1, image_count(wim_file) + 1):
        listfile = f"listfile_{name}_{image}.txt"
        kept = total = 0
        with open(listfile, "w") as out:
            for path, file_hash in list_image_files(wim_file, image):
                total += 1
                if not is_interesting(path) or file_hash in seen_hashes or file_hash == EMPTY_HASH:
                    continue
                seen_hashes.add(file_hash)
                out.write(f'"{path}"\n')
                kept += 1
        print(f"{name} image {image}: keeping {kept} of {total} files", file=sys.stderr)
        if kept > 0:
            images_with_files.append(image)

    # An empty matrix is not allowed by github actions; image 1 with an empty
    # listfile makes extract_and_parse.sh emit an empty manifest instead.
    if not images_with_files:
        images_with_files = [1]
    print(f"version_matrix=[{','.join(map(str, images_with_files))}]")


if __name__ == "__main__":
    main()
