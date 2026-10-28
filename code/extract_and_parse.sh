#!/usr/bin/bash
# Extract only the files selected by wim_dedup.py from one wim image and
# generate its manifest. Usage: extract_and_parse.sh <name> <image_index>
#
# The listfile is extracted and parsed EXTRACT_BATCH_SIZE files at a time
# (default 2000), deleting each batch before the next. A full install.wim
# image's PE files do not fit on a hosted runner next to the ~9GB wim, so peak
# disk use must stay at one batch rather than the whole image.
set -e

name=$1
image=$2
batch_size=${EXTRACT_BATCH_SIZE:-2000}
listfile="listfile_${name}_${image}.txt"
manifest="manifest_${name}_${image}.out"
paths="manifest_${name}_${image}.paths"

: >"$manifest"
: >"$paths"
if [ -s "$listfile" ]; then
	workdir=$(mktemp -d)
	trap 'rm -rf "$workdir"' EXIT
	df -h . "$workdir" >&2
	split -l "$batch_size" "$listfile" "$workdir/batch_"
	for batch in "$workdir"/batch_*; do
		wimlib-imagex extract "${name}.wim" "$image" @"$batch" --dest-dir "$workdir/files" --no-acls --preserve-dir-structure >/dev/null
		python3 ./code/pdb_finding.py "$workdir/files" "$workdir/batch.out" "$workdir/batch.paths"
		cat "$workdir/batch.out" >>"$manifest"
		cat "$workdir/batch.paths" >>"$paths"
		rm -rf "$workdir/files"
	done
fi
