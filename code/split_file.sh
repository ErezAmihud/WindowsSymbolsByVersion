#!/usr/bin/bash

destDir="."

count_images() {
  wiminfo "$1" -h | grep -oP "Image Count\s*=\s*\K[\d]+"
}

my_file=$(find "$destDir" -iname "$1.wim")
file_count=$(count_images "$my_file")
out="["
for i in $(seq 1 "$file_count"); do
    out="$out$i,"
done
out="version_matrix=${out::-1}]"
echo "$out" > a.txt
