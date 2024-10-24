#!/usr/bin/bash

tempdir=$(mktemp -d)
wimextract --dest-dir "$tempdir" "$1.wim" "$2" > /dev/null
python3 ./code/pdb_finding.py "$tempdir" "manifest_$1_$2.out"
