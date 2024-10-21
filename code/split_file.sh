#!/usr/bin/bash

destDir="./unpacked_dir"

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
mv "$my_file" "$1.wim"
