# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class SelfieAttachment:
    attachment_type: Literal["photo"]
    submitted: bool

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> SelfieAttachment:
        return cls(
            attachment_type=raw["attachment_type"],
            submitted=raw["submitted"],
        )
