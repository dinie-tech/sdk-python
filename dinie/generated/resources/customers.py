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
    """Customers resource client."""

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
        """
        Register a new customer

        Register a new customer in `creating` status, idempotent on CPF

        :param params: Request parameters.
        """
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
        """
        Create a biometrics capture session

        Generate a single-use bootstrap code for the customer-facing biometrics flow. The response includes a `session_url` the partner can embed or redirect to — the kyc-app reads the code from the URL and exchanges it for a scoped session token via `POST /biometrics/session-exchange`.

        :param customer_id: Identificador único do cliente
        :param params: Request parameters.
        """
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
        """
        List customers

        List and search customers with optional filters for `cpf`, `external_id`, and `status`
        """
        raw = self._http.request("GET", "/customers", request_options=request_options)
        return SyncCursorPage.from_response(raw, item_type=Customer.deserialize)

    def retrieve(
        self,
        customer_id: str,
        request_options: RequestOptions | None = None,
    ) -> Customer:
        """
        Retrieve a customer

        Return the full customer object including registration data, status, and KYC progress

        :param customer_id: Identificador único do cliente
        """
        raw = self._http.request(
            "GET", f"/customers/{customer_id}", request_options=request_options
        )
        return Customer.deserialize(raw)

    def retrieve_bank_account(
        self,
        customer_id: str,
        request_options: RequestOptions | None = None,
    ) -> CustomerBankAccount:
        """
        Get customer bank account

        Return the bank account currently linked to this customer, if one exists.

        :param customer_id: Identificador único do cliente
        """
        raw = self._http.request(
            "GET", f"/customers/{customer_id}/bank-account", request_options=request_options
        )
        return CustomerBankAccount.deserialize(raw)

    def start_kyc_review(
        self,
        customer_id: str,
        request_options: RequestOptions | None = None,
    ) -> None:
        """
        Submit documents for KYC review

        Signal that all KYC documents have been uploaded and are ready for review. Submits documents to the verification pipeline. Also handles resubmission after document corrections.

        :param customer_id: Identificador único do cliente
        """
        self._http.request(
            "POST", f"/customers/{customer_id}/kyc-review", request_options=request_options
        )

    def update(
        self,
        customer_id: str,
        params: UpdateCustomerRequest,
        request_options: RequestOptions | None = None,
    ) -> Customer:
        """
        Update customer data

        Update customer fields such as email or phone; `cpf`, `cnpj`, `name`, `trading_name`, and `external_id` are read-only

        :param customer_id: Identificador único do cliente
        :param params: Request parameters.
        """
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
        """
        Create or update customer bank account

        Create or update the bank account linked to this customer. This endpoint is available to biometrics session tokens so the kyc-app can collect disbursement bank data.

        :param customer_id: Identificador único do cliente
        :param params: Request parameters.
        """
        raw = self._http.request(
            "POST",
            f"/customers/{customer_id}/bank-account",
            body=CustomerBankAccountRequest.serialize_upsert_bank_account(params),
            request_options=request_options,
        )
        return CustomerBankAccount.deserialize(raw)


class CreditOffers:
    """CreditOffers sub-resource client."""

    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def list(
        self,
        customer_id: str,
        request_options: RequestOptions | None = None,
    ) -> SyncCursorPage[CreditOffer]:
        """
        List credit offers for a customer

        List credit offers for a specific customer, filterable by `status`

        :param customer_id: Identificador único do cliente
        """
        raw = self._http.request(
            "GET", f"/customers/{customer_id}/credit-offers", request_options=request_options
        )
        return SyncCursorPage.from_response(raw, item_type=deserialize_credit_offer)


class KycAttachments:
    """KycAttachments sub-resource client."""

    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def create(
        self,
        customer_id: str,
        params: Any,
        request_options: RequestOptions | None = None,
    ) -> KycAttachmentResponse:
        """
        Upload a KYC attachment

        Upload a KYC attachment for the customer via `multipart/form-data`. For document requirements, send a `file`. For data-type requirements (e.g. email), send a `value` instead.

        :param customer_id: Identificador único do cliente
        :param params: Request parameters.
        """
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
        """
        Upload a KYC selfie

        Session-only upload of a selfie for biometric validation. Counterpart of the polymorphic `/kyc-attachments` route, dedicated to selfies: `evidence_type` (`selfie`) and `attachment_type` (`photo`) are implicit, so the partner only supplies `requirement_id` (`selfie_{subject_id}`) and the `file`. Requires a session token bound to the customer — a partner bearer is denied (403), even with `kyc:upload`.

        :param customer_id: Identificador único do cliente
        :param params: Request parameters.
        """
        raw = self._http.request(
            "POST",
            f"/customers/{customer_id}/kyc-attachments/selfie",
            body=MultipartBody(
                fields={k: v for k, v in params.items() if k != "file"}, file=params.get("file")
            ),
            request_options=request_options,
        )
        return KycAttachmentResponse.deserialize(raw)
