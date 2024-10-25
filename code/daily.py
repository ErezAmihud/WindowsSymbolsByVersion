#!/usr/bin/bash

import sys
import json
from listid import listid
from get_lang import get_langs

allowed_size=int(sys.argv[1])

processed_builds = set(json.load(open("process_builds.json", "r")))
builds = listid()
builds = filter(lambda build: build.uuid not in processed_builds, builds)
builds = filter(lambda build: build.arch in ["x86", "amd64"], builds)
builds = filter(lambda build: " update " not in build.title.lower(), builds) # filter updates from the db

builds = map(lambda build: build.uuid, builds)
builds = filter(lambda uuid: "en-us" in get_langs(uuid), builds)
actual_builds = []
try:
    for i in range(allowed_size):
        actual_builds.append(next(builds))
except StopIteration:
    pass

print(actual_builds)
json.dump(actual_builds, open("a.txt", 'w'))
