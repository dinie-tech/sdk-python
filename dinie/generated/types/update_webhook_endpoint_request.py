# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class UpdateWebhookEndpointRequest:
    description: str | None = None
    events: list[Any] | None = None
    status: Literal["active", "disabled"] | None = None
    url: str | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> UpdateWebhookEndpointRequest:
        return cls(
            description=raw.get("description"),
            events=raw.get("events"),
            status=raw.get("status"),
            url=raw.get("url"),
        )

    @staticmethod
    def serialize_update(params: UpdateWebhookEndpointRequest) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if params.description is not None:
            out["description"] = params.description
        if params.events is not None:
            out["events"] = params.events
        if params.status is not None:
            out["status"] = params.status
        if params.url is not None:
            out["url"] = params.url
        return out
