import requests
import json
from typing import Dict, List

from pydantic import BaseModel, Field, ValidationError, conint


class FileInfo(BaseModel):
    sha1: str
    size: conint(gt=0)
    url: str | None = None
    uuid: str | None = None
    expire: int | None = None
    debug: str | None = None


class Response(BaseModel):
    apiVersion: str
    updateName: str
    arch: str
    build: str
    files: Dict[str, FileInfo]


class UupDumpResponse(BaseModel):
    response: Response
    jsonApiVersion: str


def parse_get(text) -> UupDumpResponse:
    try:
        return UupDumpResponse(**text).response
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error parsing text: {e}")
        raise

# TODO try with updateOnly
def get(id:str, editions = ("COREN","CORE","PROFESSIONAL","PROFESSIONALN","PPIPRO")):
    return parse_get(requests.get("https://api.uupdump.net/get.php", params={"id":id, "pack":"en-us", "edition":editions}).json()).response
