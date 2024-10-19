import requests
import json
from typing import Dict, List, Literal
from pydantic import BaseModel, Field, conint, validator

class BuildInfo(BaseModel):
    title: str
    build: str
    arch: Literal["amd64", "arm64", "x86"]
    created: int | None
    uuid: str

class Response(BaseModel):
    apiVersion: str
    builds: List[BuildInfo]

    #@validator('builds', pre=True)
    def check_build_uniqueness(cls, builds):
        build_numbers = {build['build'] for build in builds}
        if len(build_numbers) != len(builds):
            raise ValueError("Duplicate build numbers found in the response.")
        return builds

class UupDumpResponse(BaseModel):
    response: Response
    jsonApiVersion: str

def parse_listid(data) ->List[BuildInfo]:
    return UupDumpResponse(**data).response.builds

def listid() -> List[BuildInfo]:
    out = requests.get("https://api.uupdump.net/listid.php", params={"sortByDate": "1"})
    return parse_listid(out.json())

