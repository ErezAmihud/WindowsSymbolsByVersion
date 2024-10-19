#!/usr/bin/bash

uuid="c598cdd6-8d6a-4fa1-8161-8e96e362b127"
editions="core;coren;professional;professionaln"

curl "https://uupdump.net/get.php?id=$uuid&pack=en-us&edition=$editions" \
 -X POST \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "autodl=2&esd=1" \
 -o download.zip

 unzip download.zip