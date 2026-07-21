#!/usr/bin/env python3
"""Set the semicolon-joined edition list of a build as the `editions` step output.

Usage: get_editions.py <uuid>
"""

import sys

from gha import write_output
from uupdump import get_editions

if __name__ == "__main__":
    write_output("editions", ";".join(get_editions(sys.argv[1])))
