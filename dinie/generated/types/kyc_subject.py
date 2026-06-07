# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class KycSubject:
    id: str
    name: str
    subject_type: Literal["applicant", "co_owner"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> KycSubject:
        return cls(
            id=raw["id"],
            name=raw["name"],
            subject_type=raw["subject_type"],
        )
