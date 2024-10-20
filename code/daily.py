#!/usr/bin/bash

import json
from listid import listid

processed_builds = set(json.load(open("process_builds.json", "r")))
builds = listid()
builds = filter(lambda build: build.uuid in processed_builds, builds)
builds = filter(lambda build: build.arch in ["x86", "amd64"], builds)

builds_uuids = map(lambda build: build.uuid, builds)
json.dump({"uuids":builds_uuids}, open("a.txt", 'w'))
