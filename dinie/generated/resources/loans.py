# generated — do not edit
from __future__ import annotations

from ...runtime.http import SyncHttpClient
from ...runtime.paginator import SyncCursorPage
from ...runtime.request_options import RequestOptions
from ..types.create_loan_request import CreateLoanRequest
from ..types.loan import Loan
from ..types.transaction import Transaction


class Loans:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http
        self._transactions = Transactions(http)

    @property
    def transactions(self) -> Transactions:
        return self._transactions

    def create(
        self,
        params: CreateLoanRequest,
        request_options: RequestOptions | None = None,
    ) -> Loan:
        raw = self._http.request(
            "POST",
            "/loans",
            body=CreateLoanRequest.serialize_create(params),
            request_options=request_options,
        )
        return Loan.deserialize(raw)

    def retrieve(
        self,
        loan_id: str,
        request_options: RequestOptions | None = None,
    ) -> Loan:
        raw = self._http.request("GET", f"/loans/{loan_id}", request_options=request_options)
        return Loan.deserialize(raw)


class Transactions:
    def __init__(self, http: SyncHttpClient) -> None:
        self._http = http

    def list(
        self,
        loan_id: str,
        request_options: RequestOptions | None = None,
    ) -> SyncCursorPage[Transaction]:
        raw = self._http.request(
            "GET", f"/loans/{loan_id}/transactions", request_options=request_options
        )
        return SyncCursorPage.from_response(raw, item_type=Transaction.deserialize)
