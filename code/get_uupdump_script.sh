#!/usr/bin/bash

uuid=$1
editions="core;coren;professional;professionaln"

curl "https://uupdump.net/get.php?id=$uuid&pack=en-us&edition=$editions" \
 -X POST \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "autodl=2&esd=1" \
 -o download.zip

 unzip download.zip
 ./uup_download_linux.sh