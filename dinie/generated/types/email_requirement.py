# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .email_submitted import EmailSubmitted
from .kyc_subject import KycSubject


@dataclass(frozen=True, slots=True)
class EmailRequirement:
    label: str
    mandatory: bool
    requirement_id: str
    requirement_type: Literal["email"]
    subject: KycSubject
    submitted: EmailSubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> EmailRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            subject=KycSubject.deserialize(raw["subject"]),
            submitted=EmailSubmitted.deserialize(raw["submitted"]) if "submitted" in raw else None,
        )
