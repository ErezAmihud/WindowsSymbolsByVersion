uuid=64ad5ee4-fa4e-4106-a2e5-c9f1c3eb6e4a
editions="core;professional"
#editions="updateOnly"
destDir="UUPs"
tempScript="aria2_script.$RANDOM.txt"
manifestdir="manifest_dir"

mkdir $destDir
mkdir $manifestdir

echo "Retrieving aria2 script for the UUP set..."
aria2c --no-conf --console-log-level=warn --log-level=info --log="aria2_download.log" -o"$tempScript" --allow-overwrite=true --auto-file-renaming=false "https://uupdump.net/get.php?id=$uuid&pack=en-us&edition=$editions&aria2=2"
if [ $? != 0 ]; then
  echo "Failed to retrieve aria2 script"
  exit 1
fi

detectedError=`grep '#UUPDUMP_ERROR:' "$tempScript" | sed 's/#UUPDUMP_ERROR://g'`
if [ ! -z $detectedError ]; then
    echo "Unable to retrieve data from Windows Update servers. Reason: $detectedError"
    echo "If this problem persists, most likely the set you are attempting to download was removed from Windows Update servers."
    exit 1
fi

echo ""
echo "Downloading the UUP set..."
aria2c --no-conf --console-log-level=warn --log-level=info --log="aria2_download.log" -x16 -s16 -j5 -c -R -d"$destDir" -i"$tempScript"
if [ $? != 0 ]; then
  echo "We have encountered an error while downloading files."
  exit 1
fi

#set -e 
# jq --compact-output --null-input '$ARGS.positional' --args -- "${X[@]}"
#extract() {
#  case $(file --mime-type -b "$1")
#    "application/x-ms-wim")
#      7z x $1 -o"$2"
#    ;;
#    "application/*-cab-*")
#      cabextract -d"$2" $1
#    *)
#    echo "Cannot extract unsupported file type"
#    exit -1
#    ;;
#  esac
#  return 0
#}

handle_cab() {
  local tempdir="name.$RANDOM.dir"
  local manifest="$manifestdir/something$RANDOM.b"
  cabextract $1 -D $tempdir
  echo Creating manifest for $filename in $manifest
  pdblister manifest $tempdir $manifest
  echo "Delete directory"
  rm -rf $tempdir
}

count_images() {
  local count=0
  wiminfo $1 $count
  out=$?
  while [[ $out == 0 ]]
  do
    count=$count+1
    wiminfo $1 $count
    out=$?
  done
  
  #return $count
}



handle_wim() {
  
  local number=$(count_images $1)
  for i in $(seq 1 $number); do 
    local manifest="$manifestdir/something$RANDOM.b"
    local tempdir="name.$RANDOM.dir"
    echo "extracting image $i from $1"
    WIMEXTRACT --dest-dir $tempdir $1 $i
    echo Creating manifest for $filename image $i in $manifest
    pdblister manifest $tempdir $manifest
    echo "Delete directory"
    rm -rf $tempdir
  done
}


# TODO change cab to use something that is not 7zip
for filename in $destDir/*; do    
  #manifest="$manifestdir/something$RANDOM.b"
  #mkdir $tempdir
  echo "Extracting $filename"
  if [[ $(file --mime-type -b "$filename") == "application/vnd.ms-cab-compressed" ]] ; then
    handle_cab $filename
  else if [[ $(file --mime-type -b "$filename") == "application/x-ms-wim" ]] ; then
    handle_wim $filename
  else
    local mm=$(file --mime-type -b "$filename")
    echo "other mimetipe = $mm"
  fi
done



cat $manifestdir/* > manifest.out
