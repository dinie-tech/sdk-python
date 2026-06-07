# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ids import WebhookEndpointId


@dataclass(frozen=True, slots=True)
class WebhookSecretRotation:
    id: WebhookEndpointId
    previous_secret_expires_at: int
    secret: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> WebhookSecretRotation:
        return cls(
            id=raw["id"],
            previous_secret_expires_at=raw["previous_secret_expires_at"],
            secret=raw["secret"],
        )
