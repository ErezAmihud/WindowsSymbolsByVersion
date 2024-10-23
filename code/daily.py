#!/usr/bin/bash

import json
from listid import listid

processed_builds = set(json.load(open("process_builds.json", "r")))
builds = listid()
builds = filter(lambda build: build.uuid not in processed_builds, builds)
builds = filter(lambda build: build.arch in ["x86", "amd64"], builds)
builds = filter(lambda build: "cumulative update " not in build.title.lower(), builds)

builds = map(lambda build: build.uuid, builds)
builds = list(builds)
builds=builds[:2]
json.dump(builds, open("a.txt", 'w'))
