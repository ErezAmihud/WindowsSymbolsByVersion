#!/usr/bin/env python
import os
import os.path
import sys
from concurrent.futures import ProcessPoolExecutor

import pefile
import tqdm

DEBUG_DIRECTORY_INDEX = pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DEBUG"]


def get_guid(dll: pefile.PE):
    if hasattr(dll, "DIRECTORY_ENTRY_DEBUG"):
        for entry in dll.DIRECTORY_ENTRY_DEBUG:
            if (
                entry.struct.Type == pefile.DEBUG_TYPE["IMAGE_DEBUG_TYPE_CODEVIEW"]
                and entry.entry is not None
                and b"\\" not in entry.entry.PdbFileName
            ):
                signature_string = ""
                if hasattr(entry.entry, "Signature"):
                    signature_string = hex(entry.entry.Signature)[2:]
                else:
                    signature_string = entry.entry.Signature_String

                yield entry.entry.PdbFileName.rstrip(b"\x00").decode("ascii"), signature_string


def process_file(file_path):
    """Return the (pdb, guid) entries of a single file."""
    results = []
    try:
        # Cheap pre-filter: most files are not PE files at all, and raising
        # PEFormatError for each of them is much slower than this check.
        with open(file_path, "rb") as f:
            if f.read(2) != b"MZ":
                return results
        with pefile.PE(file_path, fast_load=True) as dll:
            # Only the debug directory is needed. full_load() would also parse
            # imports/exports/resources etc., which dominates the runtime on
            # resource-heavy binaries.
            dll.parse_data_directories(directories=[DEBUG_DIRECTORY_INDEX])
            results.extend(get_guid(dll))
    except (pefile.PEFormatError, FileNotFoundError):
        pass
    except Exception:
        print(f"error in {file_path}")
        raise
    return results


def list_files(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)


def traverse_directory(directory, out, paths_out=None, workers=None):
    """Traverse the directory and process each file.

    When paths_out is given, also write one `path<TAB>pdb<TAB>guid` line per
    entry, with the path relative to `directory` using forward slashes (i.e.
    the file's path inside the scanned image). Tab-separated because pdb
    names and paths may contain commas.
    """
    files = list(list_files(directory))
    with ProcessPoolExecutor(max_workers=workers or os.cpu_count()) as executor:
        results = zip(files, executor.map(process_file, files, chunksize=64))
        for file_path, rets in tqdm.tqdm(results, total=len(files), mininterval=10):
            for pdb, guid in rets:
                out.write(f"{pdb},{guid},1\n")
                if paths_out is not None:
                    rel = os.path.relpath(file_path, directory).replace(os.sep, "/")
                    paths_out.write(f"{rel}\t{pdb}\t{guid}\n")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: python script.py <directory> <out> [paths_out]")
        sys.exit(1)

    target_directory = sys.argv[1]
    target_output = sys.argv[2]
    target_paths = sys.argv[3] if len(sys.argv) == 4 else None

    if not os.path.isdir(target_directory):
        print(f"The specified path '{target_directory}' is not a directory.")
        sys.exit(1)

    with open(target_output, "w") as f:
        if target_paths is None:
            traverse_directory(target_directory, f)
        else:
            with open(target_paths, "w") as pf:
                traverse_directory(target_directory, f, pf)
