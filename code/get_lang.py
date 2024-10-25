from functools import wraps
import requests
from pydantic import BaseModel
from typing import List, Dict

class ResponseModel(BaseModel):
    langList: List[str]
    langFancyNames: Dict[str, str] | List

class SchemaModel(BaseModel):
    response: ResponseModel
    jsonApiVersion: str

def retry(times:int):
    def inner_retry(func):
        @wraps(func)
        def inner(*args, **kwargs):
            count = times
            while count > 0:
                try:
                    return func(*args, **kwargs)
                except:
                    count -= 1
                    if count == 0:
                        raise
        return inner
    return inner_retry


@retry(4)
def get_langs(uuid) -> List[str]:
    out = requests.get("https://api.uupdump.net/listlangs.php", params={"id": uuid}, allow_redirects=True)
    out.raise_for_status()
    return SchemaModel(**out.json()).response.langList

