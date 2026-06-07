# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .kyc_subject import KycSubject
from .proof_of_address_submitted import ProofOfAddressSubmitted


@dataclass(frozen=True, slots=True)
class ProofOfAddressRequirement:
    label: str
    mandatory: bool
    requirement_id: str
    requirement_type: Literal["proof_of_address"]
    subject: KycSubject
    submitted: ProofOfAddressSubmitted | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> ProofOfAddressRequirement:
        return cls(
            label=raw["label"],
            mandatory=raw["mandatory"],
            requirement_id=raw["requirement_id"],
            requirement_type=raw["requirement_type"],
            subject=KycSubject.deserialize(raw["subject"]),
            submitted=ProofOfAddressSubmitted.deserialize(raw["submitted"])
            if "submitted" in raw
            else None,
        )
