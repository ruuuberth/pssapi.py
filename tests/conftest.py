import pytest_asyncio

import pssapi.http_client as _http_client


@pytest_asyncio.fixture(autouse=True)
async def _close_default_http_client():
    """Release pooled connections after every test: each test runs on its own event loop."""
    yield
    await _http_client.close_default_http_client()
