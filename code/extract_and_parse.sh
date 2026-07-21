#!/usr/bin/bash
# Extract only the files selected by wim_dedup.py from one wim image and
# generate its manifest. Usage: extract_and_parse.sh <name> <image_index>
set -e

name=$1
image=$2
listfile="listfile_${name}_${image}.txt"
manifest="manifest_${name}_${image}.out"
paths="manifest_${name}_${image}.paths"

if [ -s "$listfile" ]; then
	tempdir=$(mktemp -d)
	wimlib-imagex extract "${name}.wim" "$image" @"$listfile" --dest-dir "$tempdir" --no-acls --preserve-dir-structure >/dev/null
	python3 ./code/pdb_finding.py "$tempdir" "$manifest" "$paths"
else
	touch "$manifest" "$paths"
fi
