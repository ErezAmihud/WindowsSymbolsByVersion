from functools import wraps
from time import sleep
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
                    sleep(1)
        return inner
    return inner_retry


@retry(4)
def get_langs(uuid) -> List[str]:
    out = requests.get("https://api.uupdump.net/listlangs.php", params={"id": uuid}, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
    out.raise_for_status()
    return SchemaModel(**out.json()).response.langList

