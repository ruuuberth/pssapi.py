# API discovery

`pssapi.discovery` converts captured Pixel Starships traffic into a portable,
repeatable description of the API. It is intentionally separate from the
runtime SDK: applications do not need capture tooling installed.

## `.psscap`

A capture is a ZIP archive containing:

- `manifest.json` — format/version and capture metadata
- `requests.jsonl` — one request observation per line
- `responses.jsonl` — one response observation per line

Records may include `id`, `service`, `method`, `path`, `http_method`, `params`,
`body`, `status`, headers, timestamps and timing information. The format keeps
raw observations so the parser can evolve without requiring a new capture.

## Analyze a capture

```python
from pssapi.discovery import DiscoveryAnalyzer

report = DiscoveryAnalyzer().analyze_capture("capture.psscap")
print(report.to_dict())
```

The first analyzer identifies endpoint names, HTTP methods, request parameters,
response fields, observed types, nullable fields and fields that were absent in
some samples. Nested objects and objects inside arrays are tracked using dotted
paths.

## Capture pipeline

The intended pipeline is:

```text
Pixel Starships
      ↓
platform capture tool
      ↓
.psscap
      ↓
normalization
      ↓
endpoint/schema observations
      ↓
API diff + code generation
      ↓
pssapi typed services/models
```

The next discovery milestones are catalog-aware string analysis, enum inference,
API version diffs, Pydantic model generation, generated service wrappers and a
CLI around these operations.
