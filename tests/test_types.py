"""Tests for NWC response types."""

from nostrnwc.types import (
    BalanceResponse,
    GetInfoResponse,
    ListTransactionsResponse,
    LookupInvoiceResponse,
    MakeInvoiceResponse,
    NWCError,
    PayResponse,
    Transaction,
)


class TestBalanceResponse:
    def test_create(self):
        r = BalanceResponse(balance=100_000)
        assert r.balance == 100_000


class TestPayResponse:
    def test_create(self):
        r = PayResponse(preimage="ab" * 32)
        assert len(r.preimage) == 64


class TestMakeInvoiceResponse:
    def test_create(self):
        r = MakeInvoiceResponse(invoice="lnbc1...", payment_hash="cd" * 32)
        assert r.invoice.startswith("lnbc")
        assert len(r.payment_hash) == 64


class TestLookupInvoiceResponse:
    def test_paid(self):
        r = LookupInvoiceResponse(invoice="lnbc1...", paid=True, preimage="ef" * 32)
        assert r.paid is True

    def test_unpaid(self):
        r = LookupInvoiceResponse(invoice="lnbc1...", paid=False)
        assert r.preimage is None


class TestTransaction:
    def test_create(self):
        tx = Transaction(
            type="incoming",
            invoice="lnbc1...",
            amount=50_000,
            fees_paid=0,
            created_at=1700000000,
        )
        assert tx.type == "incoming"
        assert tx.settled_at is None


class TestListTransactionsResponse:
    def test_empty(self):
        r = ListTransactionsResponse()
        assert r.transactions == []

    def test_with_transactions(self):
        tx = Transaction(
            type="outgoing", invoice="lnbc1...", amount=10_000,
            fees_paid=100, created_at=1700000000,
        )
        r = ListTransactionsResponse(transactions=[tx])
        assert len(r.transactions) == 1


class TestGetInfoResponse:
    def test_defaults(self):
        r = GetInfoResponse()
        assert r.alias == ""
        assert r.methods == []

    def test_with_methods(self):
        r = GetInfoResponse(methods=["pay_invoice", "get_balance"])
        assert "pay_invoice" in r.methods


class TestNWCError:
    def test_create(self):
        e = NWCError(code="INSUFFICIENT_BALANCE", message="Not enough sats")
        assert e.code == "INSUFFICIENT_BALANCE"
