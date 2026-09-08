# Modern client

The 0.8 client adds a backwards-compatible foundation for the next generation of `pssapi`.

## Goals

- Reuse one `aiohttp.ClientSession` instead of creating a session for every request.
- Keep connections alive and pool concurrent requests.
- Retry transient HTTP/network failures with exponential backoff.
- Provide bounded in-memory caching for GET requests.
- Expose a raw endpoint escape hatch while typed services are being expanded.
- Keep the existing generated services working unchanged.

## Basic usage

```python
from pssapi import PssApiClient

async with PssApiClient() as pss:
    result = await pss.raw.call(
        "CharacterService",
        "ListAllCharacterDesigns2",
        params={"deviceType": pss.device_type, "languageKey": pss.language_key},
    )
```

The raw client returns JSON as Python dictionaries/lists when the response is JSON; XML and other text responses remain strings.

## Configuration

```python
from pssapi import PssApiClient, PssApiConfig

config = PssApiConfig(
    production_server="api.pixelstarships.com",
    timeout=20,
    connect_timeout=5,
    max_connections=100,
    retries=3,
    retry_backoff=0.25,
    cache_ttl=60,
)

async with PssApiClient(config=config) as pss:
    data = await pss.raw.call("SettingService", "GetLatestVersion3")
```

Environment variables are also supported:

- `PSSAPI_PRODUCTION_SERVER`
- `PSSAPI_TIMEOUT`
- `PSSAPI_CONNECT_TIMEOUT`
- `PSSAPI_MAX_CONNECTIONS`
- `PSSAPI_MAX_KEEPALIVE_CONNECTIONS`
- `PSSAPI_RETRIES`
- `PSSAPI_RETRY_BACKOFF`
- `PSSAPI_CACHE_TTL` (`off`, `none`, or `null` disables caching)
- `PSSAPI_USER_AGENT`

## Architecture rule

The modern transport is deliberately independent of the API discovery/capture tooling planned for later milestones. Capture data may generate or validate typed services, but the runtime SDK never needs a mitmproxy dependency.

The next milestones can build on this layer with persistent caches, schema discovery, catalog handling, generated Pydantic models, and API diffing.
