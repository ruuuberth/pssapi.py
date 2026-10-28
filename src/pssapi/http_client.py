"""
Shared HTTP transport for the Pixel Starships API.

The API is fetched with a single, reusable `aiohttp.ClientSession` per event loop instead of
one session per request. Creating a session per request throws its connection pool away, so
every call pays a new TCP + TLS handshake; the aiohttp documentation recommends one session
per application. A session is bound to the event loop that created it, hence one client per
running loop.
"""

import asyncio as _asyncio
import weakref as _weakref
from typing import Any as _Any
from typing import Mapping as _Mapping
from typing import NamedTuple as _NamedTuple
from typing import Optional as _Optional
from typing import Union as _Union

import aiohttp as _aiohttp


HTTP_TIMEOUT_SECONDS: float = 30.0

_MappingOrNone = _Optional[_Mapping[str, _Any]]
_RequestBody = _Union[str, bytes, _Mapping[str, _Any], None]


class HttpResponse(_NamedTuple):
    """A fully read HTTP response: the status codes of error bodies stay available to the caller."""

    status: int
    body: bytes

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def text(self) -> str:
        return self.body.decode("utf-8")


class HttpClient:
    """
    A reusable HTTP client for the Pixel Starships API.

    Holds one `aiohttp.ClientSession` for the event loop that first uses it, so consecutive
    calls reuse pooled connections, and bounds every request with `timeout`. Responses are
    returned whole (status and body) so callers can keep using the error message the server
    sends in the body of an error response.

    Use it as an async context manager when you want to release the connections deterministically:

    ```python
    async with pssapi.http_client.HttpClient() as http_client:
        response = await http_client.get("https://api.pixelstarships.com/SettingService/GetLatestVersion3")
        print(response.status, response.text())
    ```

    An instance belongs to a single event loop. Use `pssapi.http_client.get_default_http_client()`
    to get the shared per-loop instance instead of creating your own.
    """

    def __init__(self, timeout: _Union[float, _aiohttp.ClientTimeout, None] = None) -> None:
        """
        Args:
            `timeout` (Union[float, aiohttp.ClientTimeout, None]): Total timeout in seconds for a
                request, or a configured `aiohttp.ClientTimeout`. Defaults to `HTTP_TIMEOUT_SECONDS`.
        """
        self.__timeout: _Union[float, _aiohttp.ClientTimeout] = timeout if timeout is not None else _aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        self.__session: _Optional[_aiohttp.ClientSession] = None
        self.__loop: _Optional[_asyncio.AbstractEventLoop] = None

    @property
    def session(self) -> _aiohttp.ClientSession:
        """The underlying `aiohttp.ClientSession`, created on first use."""
        return self.__ensure_session()

    @property
    def timeout(self) -> _Union[float, _aiohttp.ClientTimeout]:
        return self.__timeout

    async def get(self, url: str, params: _MappingOrNone = None) -> HttpResponse:
        async with self.__ensure_session().get(url, params=params) as response:
            return HttpResponse(response.status, await response.read())

    async def post(self, url: str, data: _RequestBody = None, params: _MappingOrNone = None) -> HttpResponse:
        async with self.__ensure_session().post(url, data=data, params=params) as response:
            return HttpResponse(response.status, await response.read())

    async def aclose(self) -> None:
        """Close the underlying session and release its connections."""
        session = self.__session
        self.__session = None
        if session is not None and not session.closed:
            await session.close()

    async def __aenter__(self) -> "HttpClient":
        self.__ensure_session()
        return self

    async def __aexit__(self, *_args) -> None:
        await self.aclose()

    def __ensure_session(self) -> _aiohttp.ClientSession:
        loop = _asyncio.get_running_loop()
        if self.__session is not None and not self.__session.closed and self.__loop is not loop:
            raise RuntimeError("This HttpClient is bound to another event loop. Create one client per event loop, or use get_default_http_client().")
        if self.__session is None or self.__session.closed:
            self.__session = _aiohttp.ClientSession(timeout=self.__timeout)
            self.__loop = loop
        return self.__session


_DEFAULT_CLIENTS: "_weakref.WeakKeyDictionary[_asyncio.AbstractEventLoop, HttpClient]" = _weakref.WeakKeyDictionary()


def get_default_http_client() -> HttpClient:
    """The `HttpClient` shared by everything running on the current event loop."""
    loop = _asyncio.get_running_loop()
    http_client = _DEFAULT_CLIENTS.get(loop)
    if http_client is None:
        http_client = HttpClient()
        _DEFAULT_CLIENTS[loop] = http_client
    return http_client


async def close_default_http_client() -> None:
    """Close and forget the default `HttpClient` of the current event loop. It is recreated on demand."""
    http_client = _DEFAULT_CLIENTS.pop(_asyncio.get_running_loop(), None)
    if http_client is not None:
        await http_client.aclose()
