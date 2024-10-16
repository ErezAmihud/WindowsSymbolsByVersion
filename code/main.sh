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

set -e 
# TODO change cab to use something that is not 7zip
for filename in $destDir/*; do
  echo Extracting $filename
  tempdir="name.$RANDOM.dir"
  manifest="$manifestdir/something$RANDOM.b"
  mkdir $tempdir
  echo "Extracting $filename"
  7z x $filename -o"$tempdir"
  ls $tempdir
  echo Creating manifest for $filename in $manifest
  pdblister manifest $tempdir $manifest
  echo Deleting not needed directory
  rm -rf $tempdir
done

cat $manifestdir/* > manifest.out
