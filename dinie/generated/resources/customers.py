# generated — do not edit
from __future__ import annotations

from typing import Any

from ...runtime.http import SyncHttpClient
from ...runtime.multipart import MultipartBody
from ...runtime.paginator import SyncCursorPage
from ...runtime.request_options import RequestOptions
from ..types.biometrics_session import BiometricsSession
from ..types.create_customer_request import CreateCustomerRequest
from ..types.credit_offer_union import CreditOffer, deserialize_credit_offer
from ..types.customer import Customer
from ..types.customer_bank_account import CustomerBankAccount
from ..types.customer_bank_account_request import CustomerBankAccountRequest
from ..types.kyc_attachment_response import KycAttachmentResponse
from ..types.update_customer_request import UpdateCustomerRequest


class Customers:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http
        self._credit_offers = CreditOffers(http)
        self._kyc_attachments = KycAttachments(http)

    @property
    def credit_offers(self) -> CreditOffers:
        return self._credit_offers

    @property
    def kyc_attachments(self) -> KycAttachments:
        return self._kyc_attachments

    def create(
        self,
        params: CreateCustomerRequest,
        request_options: RequestOptions | None = None,
    ) -> Customer:
        raw = self._http.request(
            "POST",
            "/customers",
            body=CreateCustomerRequest.serialize_create(params),
            request_options=request_options,
        )
        return Customer.deserialize(raw)

    def create_biometrics_session(
        self,
        customer_id: str,
        params: Any,
        request_options: RequestOptions | None = None,
    ) -> BiometricsSession:
        raw = self._http.request(
            "POST",
            f"/customers/{customer_id}/biometrics",
            body=params,
            request_options=request_options,
        )
        return BiometricsSession.deserialize(raw)

    def list(
        self,
        request_options: RequestOptions | None = None,
    ) -> SyncCursorPage[Customer]:
        raw = self._http.request("GET", "/customers", request_options=request_options)
        return SyncCursorPage.from_response(raw, item_type=Customer.deserialize)

    def retrieve(
        self,
        customer_id: str,
        request_options: RequestOptions | None = None,
    ) -> Customer:
        raw = self._http.request(
            "GET", f"/customers/{customer_id}", request_options=request_options
        )
        return Customer.deserialize(raw)

    def retrieve_bank_account(
        self,
        customer_id: str,
        request_options: RequestOptions | None = None,
    ) -> CustomerBankAccount:
        raw = self._http.request(
            "GET", f"/customers/{customer_id}/bank-account", request_options=request_options
        )
        return CustomerBankAccount.deserialize(raw)

    def start_kyc_review(
        self,
        customer_id: str,
        request_options: RequestOptions | None = None,
    ) -> None:
        self._http.request(
            "POST", f"/customers/{customer_id}/kyc-review", request_options=request_options
        )

    def update(
        self,
        customer_id: str,
        params: UpdateCustomerRequest,
        request_options: RequestOptions | None = None,
    ) -> Customer:
        raw = self._http.request(
            "PATCH",
            f"/customers/{customer_id}",
            body=UpdateCustomerRequest.serialize_update(params),
            request_options=request_options,
        )
        return Customer.deserialize(raw)

    def upsert_bank_account(
        self,
        customer_id: str,
        params: CustomerBankAccountRequest,
        request_options: RequestOptions | None = None,
    ) -> CustomerBankAccount:
        raw = self._http.request(
            "POST",
            f"/customers/{customer_id}/bank-account",
            body=CustomerBankAccountRequest.serialize_upsert_bank_account(params),
            request_options=request_options,
        )
        return CustomerBankAccount.deserialize(raw)


class CreditOffers:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def list(
        self,
        customer_id: str,
        request_options: RequestOptions | None = None,
    ) -> SyncCursorPage[CreditOffer]:
        raw = self._http.request(
            "GET", f"/customers/{customer_id}/credit-offers", request_options=request_options
        )
        return SyncCursorPage.from_response(raw, item_type=deserialize_credit_offer)


class KycAttachments:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self,
        customer_id: str,
        params: Any,
        request_options: RequestOptions | None = None,
    ) -> KycAttachmentResponse:
        raw = self._http.request(
            "POST",
            f"/customers/{customer_id}/kyc-attachments",
            body=MultipartBody(
                fields={k: v for k, v in params.items() if k != "file"}, file=params.get("file")
            ),
            request_options=request_options,
        )
        return KycAttachmentResponse.deserialize(raw)

    def upload_selfie(
        self,
        customer_id: str,
        params: Any,
        request_options: RequestOptions | None = None,
    ) -> KycAttachmentResponse:
        raw = self._http.request(
            "POST",
            f"/customers/{customer_id}/kyc-attachments/selfie",
            body=MultipartBody(
                fields={k: v for k, v in params.items() if k != "file"}, file=params.get("file")
            ),
            request_options=request_options,
        )
        return KycAttachmentResponse.deserialize(raw)
