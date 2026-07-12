import sys
from listid import listid


uuid = sys.argv[1]
matches = [build for build in listid() if build.uuid == uuid]
# a build can get delisted from uupdump between being picked and deployed;
# a generic name is better than losing the finished manifest
name = str(matches[0]) if matches else f"Unknown build {uuid}"
open("b.txt", "w").write(f"name={name}")
