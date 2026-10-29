#!/usr/bin/bash
# shellcheck disable=SC2329 # the run_* functions are invoked through measure
# Throwaway experiment: parse one wim image three ways on a hosted runner and
# compare each result with the manifest production made from the same wim.
#   mount   - wimlib-imagex mount (FUSE, as the runner user), parse in place
#   disk    - extract the whole listfile into the workspace (mktemp -p .)
#   batched - code/extract_and_parse.sh from PR #40 (2000-file batches in /tmp)
# Usage: compare.sh <name> <image>   (expects <name>.wim, listfile, ref/)
set -euo pipefail

name=$1
image=$2
wim="$name.wim"
listfile="listfile_${name}_${image}.txt"
summary=${GITHUB_STEP_SUMMARY:-/dev/stdout}

used() { # bytes used on the workspace disk plus /tmp
	df -B1 --output=source,used . /tmp | tail -n +2 | sort -u | awk '{s += $2} END {print s}'
}

measure() { # measure <label> <cmd...>: run cmd, record wall time and peak extra disk
	local label=$1 base peak cur start pid rc=0
	shift
	base=$(used)
	peak=$base
	start=$(date +%s)
	"$@" &
	pid=$!
	while kill -0 "$pid" 2>/dev/null; do
		cur=$(used)
		[ "$cur" -gt "$peak" ] && peak=$cur
		sleep 0.5
	done
	wait "$pid" || rc=$?
	echo "$label|$(($(date +%s) - start))|$(((peak - base) / 2 ** 20))|$rc" >>results.txt
	return 0
}

run_mount() {
	mkdir -p mnt
	wimlib-imagex mount "$wim" "$image" mnt
	local rc=0
	python3 .github/mount-test/parse_mounted.py . mnt "$listfile" mount.out mount.paths || rc=$?
	wimlib-imagex unmount mnt || fusermount3 -u mnt
	return "$rc"
}

run_disk() {
	local dir
	dir=$(mktemp -d -p "$PWD")
	wimlib-imagex extract "$wim" "$image" @"$listfile" --dest-dir "$dir" --no-acls --preserve-dir-structure >/dev/null
	python3 ./code/pdb_finding.py "$dir" disk.out disk.paths
	rm -rf "$dir"
}

run_batched() {
	bash ./code/extract_and_parse.sh "$name" "$image"
	mv "manifest_${name}_${image}.out" batched.out
	mv "manifest_${name}_${image}.paths" batched.paths
}

echo "listed files: $(wc -l <"$listfile")" >&2
: >results.txt
measure mount run_mount
measure disk run_disk
measure batched run_batched

ref_out="ref/manifest_${name}_${image}.out"
ref_paths="ref/manifest_${name}_${image}.paths"
fail=0
{
	echo "### $name image $image ($(wc -l <"$listfile") listed files, reference $(wc -l <"$ref_out") entries)"
	echo
	echo "| method | wall s | peak extra disk MiB | exit | .out = production | .paths = production |"
	echo "|---|---|---|---|---|---|"
} >table.md
while IFS='|' read -r label secs mib rc; do
	o=no
	p=no
	[ -f "$label.out" ] && cmp -s <(sort "$label.out") <(sort "$ref_out") && o=yes
	[ -f "$label.paths" ] && cmp -s <(sort "$label.paths") <(sort "$ref_paths") && p=yes
	if [ "$rc" != 0 ] || [ $o != yes ] || [ $p != yes ]; then fail=1; fi
	echo "| $label | $secs | $mib | $rc | $o | $p |" >>table.md
done <results.txt
cat table.md
cat table.md >>"$summary"
exit $fail
