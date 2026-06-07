# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class EiMeiDocumentsAttachment:
    attachment_type: Literal["ei_registration_requirement", "ccmei"]
    submitted: bool

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> EiMeiDocumentsAttachment:
        return cls(
            attachment_type=raw["attachment_type"],
            submitted=raw["submitted"],
        )
