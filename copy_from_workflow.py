import json
import typing
from zipfile import ZipFile
import requests
from listid import listid
from github import Github,Auth
if typing.TYPE_CHECKING:
    from github.Artifact import Artifact

def get_artifacts(artifacts) -> typing.Generator["Artifact", None, None]:
    for art in artifacts:
        if art.name.endswith("merged_manifest"):
            yield art

auth = Auth.Token("")
g = Github(auth=auth)
r=g.get_repo("ErezAmihud/WindowsSymbolsByVersion")
w=r.get_workflow_run("runid")

all_builds =  listid()

used = json.load(open("process_builds.json", "r"))
with open("docs/index.md", "a") as versions:
    for art in get_artifacts(w.get_artifacts()):
        print(f"processing {art.name}")
        uuid = art.name.replace("merged_manifest", "")
        name = str(list(filter(lambda build: build.uuid==uuid, all_builds))[0])

        status,headers,a_artifacts = w._requester.requestJson("GET", art.archive_download_url)
        if status == 302:
            with open("temp.zip", "wb") as zip_file:
                zip_file.write(requests.get(headers["location"]).content)
            with ZipFile('temp.zip', 'r') as myzip:
                with open(f"manifests/{uuid}.manifest", "wb") as f:
                    f.write(myzip.read("manifest.out"))
        else:
            print("Errorrrrrrr")
            continue
        #r = requests.get(art.archive_download_url)

        used.append(uuid)

        versions.write(f"({name})[../manifests/{uuid}.manifest]\n")
#print(list())

json.dump(used, open("process_builds.json", "w"))

