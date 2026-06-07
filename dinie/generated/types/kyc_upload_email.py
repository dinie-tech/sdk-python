# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class KycUploadEmail:
    attachment_type: Literal["email"]
    evidence_type: Literal["email"]
    requirement_id: str
    value: str

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> KycUploadEmail:
        return cls(
            attachment_type=raw["attachment_type"],
            evidence_type=raw["evidence_type"],
            requirement_id=raw["requirement_id"],
            value=raw["value"],
        )
