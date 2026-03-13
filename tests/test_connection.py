"""Tests for NWC connection string parsing."""

import pytest

from nostrwalletconnect.connection import NWCConnection


VALID_PUBKEY = "a" * 64
VALID_SECRET = "b" * 64
VALID_RELAY = "wss://relay.example.com"


def make_uri(pubkey=VALID_PUBKEY, relay=VALID_RELAY, secret=VALID_SECRET, lud16=None):
    uri = f"nostr+walletconnect://{pubkey}?relay={relay}&secret={secret}"
    if lud16:
        uri += f"&lud16={lud16}"
    return uri


class TestNWCConnectionParse:
    def test_parse_valid_uri(self):
        conn = NWCConnection.parse(make_uri())
        assert conn.wallet_pubkey == VALID_PUBKEY
        assert conn.relay == VALID_RELAY
        assert conn.secret == VALID_SECRET
        assert conn.lud16 is None

    def test_parse_with_lud16(self):
        conn = NWCConnection.parse(make_uri(lud16="user@wallet.com"))
        assert conn.lud16 == "user@wallet.com"

    def test_parse_invalid_scheme(self):
        with pytest.raises(ValueError, match="Invalid NWC URI"):
            NWCConnection.parse("https://example.com")

    def test_parse_missing_relay(self):
        uri = f"nostr+walletconnect://{VALID_PUBKEY}?secret={VALID_SECRET}"
        with pytest.raises(ValueError, match="Missing required 'relay'"):
            NWCConnection.parse(uri)

    def test_parse_missing_secret(self):
        uri = f"nostr+walletconnect://{VALID_PUBKEY}?relay={VALID_RELAY}"
        with pytest.raises(ValueError, match="Missing required 'secret'"):
            NWCConnection.parse(uri)

    def test_parse_invalid_pubkey_length(self):
        with pytest.raises(ValueError, match="Invalid wallet pubkey"):
            NWCConnection.parse(make_uri(pubkey="abc123"))

    def test_parse_invalid_secret_length(self):
        with pytest.raises(ValueError, match="Invalid secret"):
            NWCConnection.parse(make_uri(secret="tooshort"))


class TestNWCConnectionRoundtrip:
    def test_to_uri_roundtrip(self):
        original = make_uri()
        conn = NWCConnection.parse(original)
        assert conn.to_uri() == original

    def test_to_uri_with_lud16_roundtrip(self):
        original = make_uri(lud16="bot@wallet.com")
        conn = NWCConnection.parse(original)
        assert conn.to_uri() == original

    def test_frozen(self):
        conn = NWCConnection.parse(make_uri())
        with pytest.raises(AttributeError):
            conn.wallet_pubkey = "x" * 64
