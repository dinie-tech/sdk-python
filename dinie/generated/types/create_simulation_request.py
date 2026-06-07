# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CreateSimulationRequest:
    installment_count: int
    requested_amount: float

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CreateSimulationRequest:
        return cls(
            installment_count=raw["installment_count"],
            requested_amount=raw["requested_amount"],
        )

    @staticmethod
    def serialize_create_simulation(params: CreateSimulationRequest) -> dict[str, Any]:
        return {
            "installment_count": params.installment_count,
            "requested_amount": params.requested_amount,
        }
