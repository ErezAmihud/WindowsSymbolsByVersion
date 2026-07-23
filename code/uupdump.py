"""The single client for the uupdump.net JSON API.

All endpoints go through one session with a shared retry policy and
User-Agent; all response models live here.
"""

from typing import Literal, Optional

import requests
from pydantic import BaseModel
from requests.adapters import HTTPAdapter, Retry

API_BASE = "https://api.uupdump.net"

_session = requests.Session()
_session.headers["User-Agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)
_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=4,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
    ),
)


def _get(endpoint: str, **params) -> dict:
    out = _session.get(f"{API_BASE}/{endpoint}", params=params, timeout=60)
    out.raise_for_status()
    return out.json()


AvailableArchTypes = Literal["amd64", "arm64", "x86"]


class BuildInfo(BaseModel):
    title: str
    build: str
    arch: AvailableArchTypes
    created: Optional[int] = None
    uuid: str

    def __str__(self):
        return f"{self.title} - {self.build} - arch:{self.arch}"

    __repr__ = __str__


class _ListidResponse(BaseModel):
    builds: list[BuildInfo]


class _LangsResponse(BaseModel):
    langList: list[str]


class _EditionsResponse(BaseModel):
    editionList: list[str]


class _Envelope(BaseModel):
    response: dict


def listid() -> list[BuildInfo]:
    """All known builds, newest first."""
    data = _Envelope(**_get("listid.php", sortByDate="1")).response
    return _ListidResponse(**data).builds


def get_langs(uuid: str) -> list[str]:
    data = _Envelope(**_get("listlangs.php", id=uuid)).response
    return _LangsResponse(**data).langList


def get_editions(uuid: str, language: str = "en-us") -> list[str]:
    data = _Envelope(**_get("listeditions.php", id=uuid, lang=language)).response
    return _EditionsResponse(**data).editionList


def get_build_name(uuid: str) -> str:
    """Display name for a uuid; falls back to a generic name for builds that
    were delisted from uupdump between being picked and deployed."""
    matches = [build for build in listid() if build.uuid == uuid]
    return str(matches[0]) if matches else f"Unknown build {uuid}"
