"""
Find the unpacked Windows directory (the one containing setup.exe) and rename it
to 'unpacked_dir'. This replaces the inline Python shell step in the CI.
"""
import os
import shutil
import sys

def main():
    for name in os.listdir("."):
        if os.path.isdir(name) and os.path.exists(os.path.join(name, "setup.exe")):
            shutil.move(name, "unpacked_dir")
            print(f"Moved '{name}' -> 'unpacked_dir'")
            return
    print("ERROR: Could not find a directory containing setup.exe", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
