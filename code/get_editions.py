import sys
import requests
import json
from pydantic import BaseModel
from typing import List, Dict

class ResponseModel(BaseModel):
    apiVersion: str
    editionList: List[str]
    editionFancyNames: Dict[str, str]

class SchemaModel(BaseModel):
    response: ResponseModel
    jsonApiVersion: str

def get_editions(uuid:str, language:str) -> List[str]:
    out = requests.get("https://api.uupdump.net/listeditions.php", params={"id ": uuid, "lang":language})
    return SchemaModel(**out.json()).response.editionList


with open("a.txt", 'w') as f:
    f.write(";".join(get_editions(sys.argv[1], "en-us")))