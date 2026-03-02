"""
parse_wim.py

Uses 7-Zip to selectively extract PE files (*.dll, *.exe, *.sys, *.efi, *.mui)
from a .wim file, then extracts PDB debug info from each PE, then cleans up.

Usage:
    python -m src.parse_wim <wim_file> <output_manifest>

The script:
1. Queries 7-Zip for the list of image indexes inside the .wim file.
2. For each image index:
   a. Extracts ONLY the PE file types we care about into a temp directory.
   b. Parses each extracted PE file for PDB GUID/filename.
   c. Appends results to the output manifest.
   d. Deletes the temp directory immediately to free disk space.
3. Deduplicates the final manifest (sort + uniq).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pefile
import tqdm

# File types that may contain PDB debug directory entries
PE_EXTENSIONS = ("*.dll", "*.exe", "*.sys", "*.efi", "*.mui", "*.ocx", "*.cpl")


def get_image_count(wim_path: str) -> int:
    """Return the number of images inside the WIM file using 7-Zip."""
    result = subprocess.run(
        ["7z", "l", "-slt", wim_path],
        capture_output=True,
        text=True,
        check=True,
    )
    # 7z reports "Method = WIM" files; the image count is in the header "Images = N"  
    # Fall back to counting "Path = [N]" top-level image markers.
    match = re.search(r"^\d+ folders?, \d+ files?,", result.stdout, re.MULTILINE)
    
    # More reliable: ask wimlib or parse 7z output for image blocks
    # Count occurrences of "----------" image separators with image index lines
    # Actually 7z -slt shows "Folder = +" for each image; count unique "Block = <N>" lines
    blocks = set(re.findall(r"Block = (\d+)", result.stdout))
    count = len(blocks)
    if count == 0:
        # fallback: treat as single image
        count = 1
    return count


def extract_pe_files(wim_path: str, image_index: int, dest_dir: str) -> None:
    """
    Extract only PE file types from image <image_index> of <wim_path> into <dest_dir>.
    Uses 7-Zip's include-filter to avoid extracting the entire image.
    """
    include_args = []
    for ext in PE_EXTENSIONS:
        include_args += [f"-ir!{ext}"]

    subprocess.run(
        ["7z", "e", wim_path, f"-i#{image_index}", f"-o{dest_dir}", "-y"] + include_args,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def get_guid(pe: pefile.PE):
    """Yield (pdb_filename, guid_str) for each CodeView debug entry in the PE."""
    if not hasattr(pe, "DIRECTORY_ENTRY_DEBUG"):
        return
    for entry in pe.DIRECTORY_ENTRY_DEBUG:
        if (
            entry.struct.Type == pefile.DEBUG_TYPE["IMAGE_DEBUG_TYPE_CODEVIEW"]
            and entry.entry is not None
            and b"\\" not in entry.entry.PdbFileName
        ):
            if hasattr(entry.entry, "Signature"):
                guid_str = hex(entry.entry.Signature)[2:]
            else:
                guid_str = entry.entry.Signature_String
            yield entry.entry.PdbFileName.rstrip(b"\x00").decode("ascii"), guid_str


def process_file(file_path: str):
    """Parse a single PE file and yield (pdb_name, guid) tuples."""
    try:
        with pefile.PE(file_path, fast_load=True) as pe:
            pe.full_load()
            yield from get_guid(pe)
    except (pefile.PEFormatError, FileNotFoundError, OSError):
        pass


def parse_directory(directory: str, out_file):
    """Walk a directory, parse all PE files, and write entries to out_file."""
    all_files = list(Path(directory).rglob("*"))
    for file_path in tqdm.tqdm(all_files, mininterval=10):
        if file_path.is_file():
            for pdb_name, guid in process_file(str(file_path)):
                out_file.write(f"{pdb_name},{guid},1\n")


def parse_wim(wim_path: str, output_path: str) -> None:
    """
    Main entry point: iterate over each WIM image, extract PE files only,
    parse them, write to output_path, then clean up immediately.
    """
    image_count = get_image_count(wim_path)
    print(f"Found {image_count} image(s) in {wim_path}")

    all_entries: set[str] = set()

    for image_index in range(1, image_count + 1):
        print(f"\n--- Processing image {image_index}/{image_count} ---")
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Extracting PE files from image {image_index} to {temp_dir}...")
            try:
                extract_pe_files(wim_path, image_index, temp_dir)
            except subprocess.CalledProcessError as e:
                print(f"7z extraction failed for image {image_index}: {e.stderr.decode()}")
                continue

            print(f"Parsing PE files from image {image_index}...")
            all_files = list(Path(temp_dir).rglob("*"))
            for file_path in tqdm.tqdm(all_files, mininterval=10):
                if file_path.is_file():
                    for pdb_name, guid in process_file(str(file_path)):
                        all_entries.add(f"{pdb_name},{guid},1")
        # temp_dir is automatically deleted here by context manager

    print(f"\nWriting {len(all_entries)} unique entries to {output_path}...")
    with open(output_path, "w") as f:
        for entry in sorted(all_entries):
            f.write(entry + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Extract PDB manifest from a WIM file using 7-Zip selective extraction."
    )
    parser.add_argument("wim_file", help="Path to the WIM file")
    parser.add_argument("output", help="Output manifest file path")
    args = parser.parse_args()

    if not os.path.isfile(args.wim_file):
        print(f"Error: '{args.wim_file}' is not a file.")
        sys.exit(1)

    parse_wim(args.wim_file, args.output)


if __name__ == "__main__":
    main()
