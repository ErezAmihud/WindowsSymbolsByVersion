#!/usr/bin/env python
import os
import sys
import tqdm
import os.path, pefile, struct

def get_guid(dll: pefile.PE):
    if hasattr(dll, "DIRECTORY_ENTRY_DEBUG"):
        for entry in dll.DIRECTORY_ENTRY_DEBUG:
            if entry.struct.Type == pefile.DEBUG_TYPE["IMAGE_DEBUG_TYPE_CODEVIEW"] and b"\\" not in entry.entry.PdbFileName:
                signature_string = ""
                if hasattr(entry.entry, "Signature"):
                    signature_string = hex(entry.entry.Signature[2:])
                else:
                    signature_string = entry.entry.Signature_String

                yield entry.entry.PdbFileName.rstrip(b"\x00").decode("ascii"), signature_string


def process_file(file_path):
    """Function to process each file."""
    try:
        with pefile.PE(file_path, fast_load=True) as dll:
            dll.full_load()
            yield from get_guid(dll)
    except (pefile.PEFormatError,FileNotFoundError):
       pass
    # Add your file processing logic here

def traverse_directory(directory,out):
    """Traverse the directory and process each file."""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                for ret in process_file(file_path):
                    if ret is not None:
                        out.write(f"{ret[0]},{ret[1]},1\n")
            except:
                print(f"error in {file_path}")
                raise
            yield



if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <directory> <out>")
        sys.exit(1)

    target_directory = sys.argv[1]
    target_output = sys.argv[2]

    if not os.path.isdir(target_directory):
        print(f"The specified path '{target_directory}' is not a directory.")
        sys.exit(1)

    file_count = sum(len(files) for _, _, files in os.walk(target_directory))

    with open(target_output, "w") as f:
        for i in tqdm.tqdm(traverse_directory(target_directory, f),total=file_count, mininterval=10):
           pass

