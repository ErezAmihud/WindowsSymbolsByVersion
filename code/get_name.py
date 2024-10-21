import sys
from listid import listid


uuid = sys.argv[1]
out = list(filter(lambda build: build.uuid==uuid, listid()))
assert len(out) == 1
open("b.txt", "w").write(f"name={str(out)}")