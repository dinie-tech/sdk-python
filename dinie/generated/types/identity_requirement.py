# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .identity_submitted_union import IdentitySubmitted, deserialize_identity_submitted
from .kyc_subject import KycSubject


@dataclass(frozen=True, slots=True)
class IdentityRequirement:
    label: str
    mandatory: bool
    requirement_id: str
    requirement_type: Literal["identity"]
    subject: KycSubject
    submitted: IdentitySubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> IdentityRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            subject=KycSubject.deserialize(raw["subject"]),
            submitted=deserialize_identity_submitted(raw["submitted"])
            if "submitted" in raw
            else None,
        )
