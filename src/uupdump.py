import requests
from typing import Dict, List, Literal
from pydantic import BaseModel, ValidationError, conint
from tenacity import retry, wait_fixed, stop_after_attempt
import json

class BuildInfo(BaseModel):
    title: str
    build: str
    arch: Literal["amd64", "arm64", "x86"]
    created: int | None = None
    uuid: str

    def __str__(self):
        return f"{self.title} - {self.build} - arch:{self.arch}"
    def __repr__(self):
        return f"{self.title} - {self.build} - arch:{self.arch}"

class ListIdResponse(BaseModel):
    apiVersion: str
    builds: List[BuildInfo]

class UupDumpListIdResponse(BaseModel):
    response: ListIdResponse
    jsonApiVersion: str

def parse_listid(data) -> List[BuildInfo]:
    return UupDumpListIdResponse(**data).response.builds

@retry(stop=stop_after_attempt(4), wait=wait_fixed(1))
def get_listid() -> List[BuildInfo]:
    out = requests.get("https://api.uupdump.net/listid.php", params={"sortByDate": "1"})
    out.raise_for_status()
    return parse_listid(out.json())

class LangResponseModel(BaseModel):
    langList: List[str]
    langFancyNames: Dict[str, str] | List

class LangSchemaModel(BaseModel):
    response: LangResponseModel
    jsonApiVersion: str

@retry(stop=stop_after_attempt(4), wait=wait_fixed(1))
def get_langs(uuid: str) -> List[str]:
    out = requests.get(
        "https://api.uupdump.net/listlangs.php", 
        params={"id": uuid}, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
    )
    out.raise_for_status()
    return LangSchemaModel(**out.json()).response.langList

class EditionsResponseModel(BaseModel):
    apiVersion: str
    editionList: List[str]
    editionFancyNames: Dict[str, str]

class EditionsSchemaModel(BaseModel):
    response: EditionsResponseModel
    jsonApiVersion: str

@retry(stop=stop_after_attempt(4), wait=wait_fixed(1))
def get_editions(uuid:str, language:str) -> List[str]:
    out = requests.get("https://api.uupdump.net/listeditions.php", params={"id": uuid, "lang":language})
    out.raise_for_status()
    return EditionsSchemaModel(**out.json()).response.editionList


class FileInfo(BaseModel):
    sha1: str
    size: conint(gt=0)
    url: str | None = None
    uuid: str | None = None
    expire: int | None = None
    debug: str | None = None

class GetResponse(BaseModel):
    apiVersion: str
    updateName: str
    arch: str
    build: str
    files: Dict[str, FileInfo]

class UupDumpGetResponse(BaseModel):
    response: GetResponse
    jsonApiVersion: str

@retry(stop=stop_after_attempt(4), wait=wait_fixed(1))
def get_build_files(id:str, pack:str="en-us", editions=("COREN","CORE","PROFESSIONAL","PROFESSIONALN","PPIPRO")) -> GetResponse:
    out = requests.get("https://api.uupdump.net/get.php", params={"id":id, "pack":pack, "edition":";".join(editions)})
    out.raise_for_status()
    try:
        return UupDumpGetResponse(**out.json()).response
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error parsing text: {e}")
        raise
