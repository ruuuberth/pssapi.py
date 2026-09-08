"""API endpoint and schema inference from .psscap captures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from pssapi.discovery.capture import CaptureReader
from pssapi.discovery.normalize import decode_body, normalize_endpoint


@dataclass(slots=True)
class FieldSchema:
    name: str
    types: set[str] = field(default_factory=set)
    nullable: bool = False
    occurrences: int = 0

    @property
    def type_name(self) -> str:
        if not self.types:
            return "unknown"
        if len(self.types) == 1:
            return next(iter(self.types))
        return " | ".join(sorted(self.types))


@dataclass(slots=True)
class EndpointSchema:
    endpoint: str
    methods: set[str] = field(default_factory=set)
    request_params: set[str] = field(default_factory=set)
    response_fields: dict[str, FieldSchema] = field(default_factory=dict)
    samples: int = 0

    @property
    def optional_response_fields(self) -> set[str]:
        return {name for name, item in self.response_fields.items() if item.occurrences < self.samples}


@dataclass(slots=True)
class DiscoveryReport:
    endpoints: dict[str, EndpointSchema]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoints": {
                name: {
                    "methods": sorted(schema.methods),
                    "request_params": sorted(schema.request_params),
                    "samples": schema.samples,
                    "optional_response_fields": sorted(schema.optional_response_fields),
                    "response_fields": {
                        key: {
                            "types": sorted(value.types),
                            "type": value.type_name,
                            "nullable": value.nullable,
                            "occurrences": value.occurrences,
                        }
                        for key, value in schema.response_fields.items()
                    },
                }
                for name, schema in sorted(self.endpoints.items())
            }
        }


def infer_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


class DiscoveryAnalyzer:
    """Accumulate endpoint and response-shape observations from captures."""

    def analyze_records(self, requests: Iterable[Mapping[str, Any]], responses: Iterable[Mapping[str, Any]]) -> DiscoveryReport:
        report = DiscoveryReport(endpoints={})
        request_by_id = {str(r.get("id")): r for r in requests if r.get("id") is not None}
        for response in responses:
            request_id = response.get("id", response.get("request_id"))
            request = request_by_id.get(str(request_id), response)
            endpoint = normalize_endpoint(request.get("service"), request.get("method"), request.get("path"))
            schema = report.endpoints.setdefault(endpoint, EndpointSchema(endpoint=endpoint))
            schema.samples += 1
            schema.methods.add(str(request.get("http_method", "GET")).upper())
            params = request.get("params")
            if isinstance(params, Mapping):
                schema.request_params.update(str(key) for key in params)
            body = decode_body(response.get("body"), gzipped=bool(response.get("response_gzipped")))
            self._observe_fields(schema.response_fields, body)
        return report

    def analyze_capture(self, path: str) -> DiscoveryReport:
        reader = CaptureReader(path)
        return self.analyze_records(reader.requests(), reader.responses())

    def _observe_fields(self, fields: dict[str, FieldSchema], value: Any, prefix: str = "") -> None:
        if not isinstance(value, dict):
            return
        for key, child in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            field_schema = fields.setdefault(name, FieldSchema(name=name))
            field_schema.occurrences += 1
            field_schema.types.add(infer_type(child))
            field_schema.nullable |= child is None
            if isinstance(child, dict):
                self._observe_fields(fields, child, name)
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, dict):
                        self._observe_fields(fields, item, name + "[]")
