# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BiometricsSession:
    expires_at: int
    session_url: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> BiometricsSession:
        return cls(
            expires_at=raw["expires_at"],
            session_url=raw["session_url"],
        )
