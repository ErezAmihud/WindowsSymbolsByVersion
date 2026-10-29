#!/usr/bin/bash
# Parse only the files selected by wim_dedup.py from one wim image and
# generate its manifest. Usage: extract_and_parse.sh <name> <image_index>
#
# The image is mounted read-only (wimlib's FUSE mount) and parsed in place
# rather than extracted. An install.wim image's PE files take ~8GB, more than
# fits in /tmp on some hosted runners (a 7.9GB tmpfs), and the parser only
# reads each file's headers and debug directory, so mounting writes nothing
# and is faster than extracting.
set -e

name=$1
image=$2
listfile="listfile_${name}_${image}.txt"
manifest="manifest_${name}_${image}.out"
paths="manifest_${name}_${image}.paths"

if [ -s "$listfile" ]; then
	mountpoint=$(mktemp -d)
	wimlib-imagex mount "${name}.wim" "$image" "$mountpoint"
	trap 'wimlib-imagex unmount "$mountpoint" && rmdir "$mountpoint"' EXIT
	python3 ./code/pdb_finding.py "$mountpoint" "$manifest" "$paths" --listfile "$listfile"
else
	touch "$manifest" "$paths"
fi
