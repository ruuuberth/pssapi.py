import asyncio
import base64
import gzip
from types import SimpleNamespace
from typing import Optional

import aiohttp
import pytest
from aiohttp import web

import pssapi.core as _core
import pssapi.entities as _entities
import pssapi.http_client as _http_client
import pssapi.utils.exceptions as _exceptions


XML: str = '<Setting ProductionServer="api.pixelstarships.com"/>'


@pytest.fixture
async def api_server() -> SimpleNamespace:
    """A local HTTP server that records the TCP connection of every request it serves."""
    transports = []

    async def get_xml(request: web.Request) -> web.Response:
        transports.append(id(request.transport))
        return web.Response(text=XML, content_type="application/xml")

    async def get_gzipped(request: web.Request) -> web.Response:
        transports.append(id(request.transport))
        return web.Response(text=base64.b64encode(gzip.compress(XML.encode("utf-8"))).decode("ascii"))

    async def get_error(request: web.Request) -> web.Response:
        transports.append(id(request.transport))
        return web.Response(status=500, text="<html>Internal Server Error</html>", content_type="text/html")

    app = web.Application()
    app.router.add_get("/xml", get_xml)
    app.router.add_get("/gzipped", get_gzipped)
    app.router.add_get("/error", get_error)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = runner.addresses[0][1]
    try:
        yield SimpleNamespace(base_url=f"http://127.0.0.1:{port}", transports=transports)
    finally:
        await runner.cleanup()


class _StubHttpClient(_http_client.HttpClient):
    """Returns a canned response instead of touching the network."""

    def __init__(self, response: Optional[_http_client.HttpResponse] = None) -> None:
        super().__init__()
        self.response = response
        self.urls: list = []

    async def get(self, url: str, params=None) -> "_http_client.HttpResponse":
        self.urls.append(url)
        return self.response

    async def post(self, url: str, data=None, params=None) -> "_http_client.HttpResponse":
        self.urls.append(url)
        return self.response


async def test_http_client_reuses_the_connection_for_consecutive_requests(api_server: SimpleNamespace):
    http_client = _http_client.HttpClient()

    await http_client.get(f"{api_server.base_url}/xml")
    await http_client.get(f"{api_server.base_url}/xml")
    await http_client.get(f"{api_server.base_url}/xml")

    assert len(api_server.transports) == 3
    assert len(set(api_server.transports)) == 1, "every request reused the same TCP connection"

    await http_client.aclose()


async def test_one_session_per_request_does_not_reuse_the_connection(api_server: SimpleNamespace):
    """The behaviour before HttpClient: a session (and its pool) per request."""
    for _ in range(2):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_server.base_url}/xml") as response:
                await response.read()

    assert len(set(api_server.transports)) == 2


async def test_http_client_recreates_a_closed_session(api_server: SimpleNamespace):
    http_client = _http_client.HttpClient()
    await http_client.get(f"{api_server.base_url}/xml")
    first_session = http_client.session

    await http_client.aclose()

    assert (await http_client.get(f"{api_server.base_url}/xml")).text() == XML
    assert http_client.session is not first_session

    await http_client.aclose()


async def test_http_client_refuses_to_run_on_another_event_loop(api_server: SimpleNamespace):
    http_client = _http_client.HttpClient()
    await http_client.get(f"{api_server.base_url}/xml")

    def get_from_another_loop() -> "_http_client.HttpResponse":
        return asyncio.run(http_client.get(f"{api_server.base_url}/xml"))

    with pytest.raises(RuntimeError, match="bound to another event loop"):
        await asyncio.get_running_loop().run_in_executor(None, get_from_another_loop)

    await http_client.aclose()


async def test_http_client_reports_the_status_of_an_error_response(api_server: SimpleNamespace):
    response = await _http_client.HttpClient().get(f"{api_server.base_url}/error")

    assert response.status == 500
    assert not response.ok


async def test_get_entities_from_path_uses_the_http_client_it_is_given():
    http_client = _StubHttpClient(response=_http_client.HttpResponse(200, XML.encode("utf-8")))

    result = await _core.get_entities_from_path(((_entities.Setting, "Setting", False),), "Setting", "api.pixelstarships.com", "SettingService/GetLatestVersion3", "GET", http_client=http_client)

    assert result.production_server == "api.pixelstarships.com"
    assert http_client.urls == ["https://api.pixelstarships.com/SettingService/GetLatestVersion3"]


async def test_get_entities_from_path_decodes_a_gzipped_response():
    http_client = _StubHttpClient(response=_http_client.HttpResponse(200, base64.b64encode(gzip.compress(XML.encode("utf-8")))))

    result = await _core.get_entities_from_path(
        ((_entities.Setting, "Setting", False),), "Setting", "api.pixelstarships.com", "SettingService/GetLatestVersion3", "GET", response_gzipped=True, http_client=http_client
    )

    assert result.production_server == "api.pixelstarships.com"


async def test_get_entities_from_path_rejects_an_unsupported_method():
    http_client = _StubHttpClient(response=_http_client.HttpResponse(200, XML.encode("utf-8")))

    with pytest.raises(ValueError, match="Unsupported HTTP method 'PUT'"):
        await _core.get_entities_from_path((), None, "api.pixelstarships.com", "SettingService/GetLatestVersion3", "PUT", http_client=http_client)


async def test_get_entities_from_path_reports_the_http_status_of_a_plain_error_body():
    http_client = _StubHttpClient(response=_http_client.HttpResponse(500, b"<html>Internal Server Error</html>"))

    with pytest.raises(_exceptions.PssApiError, match="HTTP 500"):
        await _core.get_entities_from_path((), None, "api.pixelstarships.com", "SettingService/GetLatestVersion3", "GET", http_client=http_client)


async def test_get_entities_from_path_keeps_the_error_message_of_the_server():
    """Error responses carry the real reason in an `errorMessage` attribute: do not lose it behind the status code."""
    body = b'<UserService errorCode="400" errorMessage="player@example.com"/>'
    http_client = _StubHttpClient(response=_http_client.HttpResponse(400, body))

    with pytest.raises(_exceptions.PssApiError, match="player@example.com"):
        await _core.get_entities_from_path((), None, "api.pixelstarships.com", "UserService/DeviceLogin17", "POST", http_client=http_client)


async def test_default_http_client_is_shared_by_everything_on_the_event_loop():
    first = _http_client.get_default_http_client()
    second = _http_client.get_default_http_client()

    assert first is second

    await _http_client.close_default_http_client()

    assert _http_client.get_default_http_client() is not first
