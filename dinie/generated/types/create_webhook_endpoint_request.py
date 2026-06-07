# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CreateWebhookEndpointRequest:
    url: str
    description: str | None = None
    events: list[Any] | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CreateWebhookEndpointRequest:
        return cls(
            description=raw.get("description"),
            events=raw.get("events"),
            url=raw["url"],
        )

    @staticmethod
    def serialize_create(params: CreateWebhookEndpointRequest) -> dict[str, Any]:
        out: dict[str, Any] = {"url": params.url}
        if params.description is not None:
            out["description"] = params.description
        if params.events is not None:
            out["events"] = params.events
        return out
