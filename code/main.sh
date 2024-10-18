#! /bin/bash
uuid=64ad5ee4-fa4e-4106-a2e5-c9f1c3eb6e4a
editions="core;professional"
#editions="updateOnly"
destDir="UUPs"
tempScript="aria2_script.$RANDOM.txt"
manifestdir="manifest_dir"

get_links(){
  # 1 == file to download to, 2 == uuid 3 == versions
  echo "Retrieving aria2 script for the UUP set..."
 # echo aria2c --no-conf --console-log-level=warn --log-level=info --log="aria2_download.log" -o "$1" --allow-overwrite=true --auto-file-renaming=false "https://uupdump.net/get.php?id=$2&pack=en-us&edition=$3&aria2=2"
  aria2c --no-conf --console-log-level=warn --log-level=info --log="aria2_download.log" -o"$tempScript" --allow-overwrite=true --auto-file-renaming=false "https://uupdump.net/get.php?id=$uuid&pack=en-us&edition=$editions&aria2=2"

#  aria2c --no-conf --console-log-level=warn --log-level=info --log="aria2_download.log" -o "$1" --allow-overwrite=true --auto-file-renaming=false "https://uupdump.net/get.php?id=$2&pack=en-us&edition=$3&aria2=2"
  if [ $? != 0 ]; then
    echo "Failed to retrieve aria2 script"
    exit 1
  fi

  detectedError=$(grep '#UUPDUMP_ERROR:' "$tempScript" | sed 's/#UUPDUMP_ERROR://g')
  if [ ! -z $detectedError ]; then
      echo "Unable to retrieve data from Windows Update servers. Reason: $detectedError"
      echo "If this problem persists, most likely the set you are attempting to download was removed from Windows Update servers."
      exit 1
  fi
}

download_uup_files() {
  # 1 == dest dir 2 == aria2 script
  echo ""
  echo "Downloading the UUP set..."
  aria2c --no-conf --console-log-level=warn --log-level=info --log="aria2_download.log" -x16 -s16 -j5 -c -d "$1" -i "$2" -m 20
  if [ $? != 0 ]; then
    echo "We have encountered an error while downloading files."
    exit 1
  fi
}

handle_cab() {
  local tempdir="name.$RANDOM.dir"
  local manifest="$manifestdir/something$RANDOM.b"
  cabextract "$1" -D $tempdir
  echo Creating manifest for "$filename" in $manifest
  pdblister manifest $tempdir $manifest
  echo "Delete directory"
  rm -rf $tempdir
}

count_images() {
  wiminfo "$1" -h | grep -oP "Image Count\s*=\s*\K[\d]+"
}

handle_wim() {
  
  number=$(count_images "$1")
  for i in $(seq 1 "$number")
  do
    local manifest="$manifestdir/something$RANDOM.b"
    local tempdir="name.$RANDOM.dir"
    echo "extracting image $i from $1"
    wimextract --dest-dir $tempdir "$1" "$i"
    echo Creating manifest for "$filename" image "$i" in $manifest  
    pdblister manifest $tempdir $manifest
    echo "Delete directory"
    rm -rf $tempdir
  done
}

# TODO change cab to use something that is not 7zip
process_files(){
for filename in "$destDir"/*; do    
  #manifest="$manifestdir/something$RANDOM.b"
  #mkdir $tempdir
  echo "Extracting $filename"
  if [[ $(file --mime-type -b "$filename") == "application/vnd.ms-cab-compressed" ]] ; then
    echo "cab"
    #handle_cab "$filename"
  elif [[ $(file --mime-type -b "$filename") == "application/x-ms-wim" ]] ; then
    #c=$(count_images $filename)
    #echo "$filename image count is $c" 
    handle_wim "$filename"
  else
    echo "other mimetipe = $(file --mime-type -b "$filename")"
  fi
done
}


main() {
  mkdir $destDir
  mkdir $manifestdir

  get_links "$tempScript" "$uuid" "$editions"
  download_uup_files "$destDir" "$tempScript"
  process_files
  cat $manifestdir/* > manifest.out
}

main