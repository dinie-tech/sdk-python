# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CredentialsListParams:
    pass

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CredentialsListParams:
        return cls()
