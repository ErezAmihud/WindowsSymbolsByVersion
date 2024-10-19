#!/usr/bin/bash
destDir=$(mktemp -d)
manifestdir="manifest_directory" # $(mktemp -d)


count_images() {
  wiminfo "$1" -h | grep -oP "Image Count\s*=\s*\K[\d]+"
}

handle_wim() {
  number=$(count_images "$1")
  for i in $(seq 1 "$number")
  do
    local manifest="$manifestdir/something$RANDOM.b"
    local tempdir="$(mktemp -d)"
    echo "extracting image $i from $1 to $tempdir"
    wimextract --dest-dir "$tempdir" "$1" "$i" > /dev/null
    #7z x -o "$tempdir" "$1" @1
    if [ $? != 0 ]; then
      echo "Failed to extract wim"
      exit 1
    fi
    echo Creating manifest for "$filename" image "$i" in "$manifest"
    python3 ./code/pdb_finding.py "$tempdir" "$manifest"
    if [ $? != 0 ]; then
      ##
      echo "==================================================="
      echo "We have a problem creating the manifest file"
      ##
      #exit 1
    fi
    echo "Delete directory"
    rm -rf "$tempdir"
  done
}

process_single_file(){
  if [[ $(file --mime-type -b "$1") == "application/x-ms-wim" ]] ; then
    echo "Extracting $1"
    #handle_wim "$1"
  #else
  #  echo "other mimetipe = $(file --mime-type -b "$1")"
  fi
}

process_files(){
local manifest="$manifestdir/something$RANDOM.b"
echo ""
echo "Checking files in original iso"
python3 ./code/pdb_finding.py $destDir $manifest
for filename in $(find "$destDir"); do
  process_single_file "$filename"
done
}

mkdir "$manifestdir"
echo "Using $manifestdir and $destDir"
b="$(find . -iname '*.iso')"
7z x "$b" -o"$destDir"
process_files
cat "$manifestdir"/* > manifest.out