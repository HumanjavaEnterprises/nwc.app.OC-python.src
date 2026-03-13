"""Parse nostr+walletconnect:// connection URIs (NIP-47)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

_HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class NWCConnection:
    """Parsed NWC connection string.

    A connection string looks like:
        nostr+walletconnect://<wallet_pubkey>?relay=wss://...&secret=<hex_privkey>

    Attributes:
        wallet_pubkey: Hex public key of the wallet service.
        relay: WebSocket URL of the relay used for communication.
        secret: Hex private key for the client side of the connection.
        lud16: Optional Lightning address of the wallet.
    """

    wallet_pubkey: str
    relay: str
    secret: str
    lud16: str | None = None

    @classmethod
    def parse(cls, connection_string: str) -> NWCConnection:
        """Parse a nostr+walletconnect:// URI into its components.

        Args:
            connection_string: Full NWC connection string.

        Returns:
            NWCConnection with wallet_pubkey, relay, secret, and optional lud16.

        Raises:
            ValueError: If the URI scheme or required parameters are missing.
        """
        if not connection_string.startswith("nostr+walletconnect://"):
            raise ValueError(
                f"Invalid NWC URI — expected 'nostr+walletconnect://' scheme, "
                f"got: {connection_string[:30]}..."
            )

        # Replace custom scheme with https so urlparse handles it correctly
        normalized = connection_string.replace("nostr+walletconnect://", "https://", 1)
        parsed = urlparse(normalized)

        wallet_pubkey = parsed.hostname
        if not wallet_pubkey or not _HEX64_RE.match(wallet_pubkey):
            raise ValueError(
                "Invalid wallet pubkey in NWC URI — expected exactly 64 hex characters"
            )

        params = parse_qs(parsed.query)

        relay_list = params.get("relay")
        if not relay_list:
            raise ValueError("Missing required 'relay' parameter in NWC URI")
        relay = relay_list[0]

        secret_list = params.get("secret")
        if not secret_list:
            raise ValueError("Missing required 'secret' parameter in NWC URI")
        secret = secret_list[0]
        if not _HEX64_RE.match(secret):
            raise ValueError(
                "Invalid secret in NWC URI — expected exactly 64 hex characters"
            )

        lud16_list = params.get("lud16")
        lud16 = lud16_list[0] if lud16_list else None

        return cls(
            wallet_pubkey=wallet_pubkey,
            relay=relay,
            secret=secret,
            lud16=lud16,
        )

    def to_uri(self) -> str:
        """Serialize back to a nostr+walletconnect:// URI."""
        uri = f"nostr+walletconnect://{self.wallet_pubkey}?relay={self.relay}&secret={self.secret}"
        if self.lud16:
            uri += f"&lud16={self.lud16}"
        return uri
