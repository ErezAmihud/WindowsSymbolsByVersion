import requests
from pydantic import BaseModel
from typing import List, Dict

class ResponseModel(BaseModel):
    langList: List[str]
    langFancyNames: Dict[str, str] | List

class SchemaModel(BaseModel):
    response: ResponseModel
    jsonApiVersion: str

def get_langs(uuid) -> List[str]:
    out = requests.get("https://api.uupdump.net/listlangs.php", params={"id": uuid}, allow_redirects=True)
    out.raise_for_status()
    return SchemaModel(**out.json()).response.langList

