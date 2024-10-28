#!/usr/bin/bash

import sys
import json
from listid import listid
from get_lang import get_langs

allowed_size=int(sys.argv[1])

processed_builds = set(json.load(open("process_builds.json", "r")))
processed_builds.union(set(json.load(open("problematic.json", "r"))))
builds = listid()
builds = filter(lambda build: build.uuid not in processed_builds, builds)
builds = filter(lambda build: build.arch in ["x86", "amd64"], builds)
builds = filter(lambda build: " insider " not in build.title.lower(), builds) # filter insider or preview
builds = filter(lambda build: " preview " not in build.title.lower(), builds) # filter insider or preview
#builds = filter(lambda build: " update " not in build.title.lower(), builds) # filter updates from the db

builds = filter(lambda build: "en-us" in get_langs(build.uuid), builds)
actual_builds = []
try:
    for i in range(allowed_size):
        build = next(builds)
        print(build.uuid, str(build))
        actual_builds.append(build.uuid)
except StopIteration:
    pass

print(actual_builds)
json.dump(actual_builds, open("a.txt", 'w'))
