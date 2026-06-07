# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Bank:
    display_name: str
    id: str
    name: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> Bank:
        return cls(
            display_name=raw["display_name"],
            id=raw["id"],
            name=raw["name"],
        )
