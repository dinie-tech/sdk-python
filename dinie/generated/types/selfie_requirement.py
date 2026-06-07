# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .kyc_subject import KycSubject
from .selfie_submitted import SelfieSubmitted


@dataclass(frozen=True, slots=True)
class SelfieRequirement:
    label: str
    mandatory: bool
    requirement_id: str
    requirement_type: Literal["selfie"]
    subject: KycSubject
    submitted: SelfieSubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> SelfieRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            subject=KycSubject.deserialize(raw["subject"]),
            submitted=SelfieSubmitted.deserialize(raw["submitted"]) if "submitted" in raw else None,
        )
