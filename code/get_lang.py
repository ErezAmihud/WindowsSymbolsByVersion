import requests
from pydantic import BaseModel
from typing import List, Dict

class ResponseModel(BaseModel):
    apiVersion: str
    langList: List[str]
    langFancyNames: Dict[str, str]

class SchemaModel(BaseModel):
    response: ResponseModel
    jsonApiVersion: str

def get_langs(uuid) -> List[str]:
    out = requests.get("https://api.uupdump.net/listlangs.php", params={"id ": uuid})
    return SchemaModel(**out.json()).response.langList

