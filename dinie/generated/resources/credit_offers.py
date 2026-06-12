# generated — do not edit
from __future__ import annotations

from ...runtime.http import SyncHttpClient
from ...runtime.paginator import SyncCursorPage
from ...runtime.request_options import RequestOptions
from ..types.create_simulation_request import CreateSimulationRequest
from ..types.credit_offer_union import CreditOffer, deserialize_credit_offer
from ..types.simulation import Simulation


class CreditOffers:
    """CreditOffers resource client."""

    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create_simulation(
        self,
        credit_offer_id: str,
        params: CreateSimulationRequest,
        request_options: RequestOptions | None = None,
    ) -> Simulation:
        """
        Simulate a loan

        Simulate a loan scenario for a credit offer, returning installment value, fees, and total cost

        :param credit_offer_id: Identificador único da oferta de crédito
        :param params: Request parameters.
        """
        raw = self._http.request(
            "POST",
            f"/credit-offers/{credit_offer_id}/simulations",
            body=CreateSimulationRequest.serialize_create_simulation(params),
            request_options=request_options,
        )
        return Simulation.deserialize(raw)

    def list(
        self,
        request_options: RequestOptions | None = None,
    ) -> SyncCursorPage[CreditOffer]:
        """
        List credit offers

        List credit offers across all customers, filterable by `customer_id` and `status`
        """
        raw = self._http.request("GET", "/credit-offers", request_options=request_options)
        return SyncCursorPage.from_response(raw, item_type=deserialize_credit_offer)

    def retrieve(
        self,
        credit_offer_id: str,
        request_options: RequestOptions | None = None,
    ) -> CreditOffer:
        """
        Retrieve a credit offer

        Return the full credit offer object with approved amount, interest rate, and validity

        :param credit_offer_id: Identificador único da oferta de crédito
        """
        raw = self._http.request(
            "GET", f"/credit-offers/{credit_offer_id}", request_options=request_options
        )
        return deserialize_credit_offer(raw)
