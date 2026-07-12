#!/usr/bin/env python
import os
import sys
import tqdm
import os.path, pefile
from concurrent.futures import ProcessPoolExecutor

DEBUG_DIRECTORY_INDEX = pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DEBUG"]


def get_guid(dll: pefile.PE):
    if hasattr(dll, "DIRECTORY_ENTRY_DEBUG"):
        for entry in dll.DIRECTORY_ENTRY_DEBUG:
            if entry.struct.Type == pefile.DEBUG_TYPE["IMAGE_DEBUG_TYPE_CODEVIEW"] and entry.entry is not None and b"\\" not in entry.entry.PdbFileName:
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


def traverse_directory(directory, out, workers=None):
    """Traverse the directory and process each file."""
    files = list(list_files(directory))
    with ProcessPoolExecutor(max_workers=workers or os.cpu_count()) as executor:
        for rets in tqdm.tqdm(executor.map(process_file, files, chunksize=64), total=len(files), mininterval=10):
            for ret in rets:
                out.write(f"{ret[0]},{ret[1]},1\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <directory> <out>")
        sys.exit(1)

    target_directory = sys.argv[1]
    target_output = sys.argv[2]

    if not os.path.isdir(target_directory):
        print(f"The specified path '{target_directory}' is not a directory.")
        sys.exit(1)

    with open(target_output, "w") as f:
        traverse_directory(target_directory, f)
