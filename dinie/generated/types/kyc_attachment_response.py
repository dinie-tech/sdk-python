# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class KycAttachmentResponse:
    attachment_type: str
    submitted: bool

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> KycAttachmentResponse:
        return cls(
            attachment_type=raw["attachment_type"],
            submitted=raw["submitted"],
        )
