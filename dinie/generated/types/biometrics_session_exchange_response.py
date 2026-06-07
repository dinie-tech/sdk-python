# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class BiometricsSessionExchangeResponse:
    access_token: str
    customer_id: str
    expires_in: int
    token_type: Literal["bearer"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> BiometricsSessionExchangeResponse:
        return cls(
            access_token=raw["access_token"],
            customer_id=raw["customer_id"],
            expires_in=raw["expires_in"],
            token_type=raw["token_type"],
        )
