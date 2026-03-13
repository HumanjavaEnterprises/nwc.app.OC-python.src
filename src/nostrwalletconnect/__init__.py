"""NostrWalletConnect — Nostr Wallet Connect (NIP-47) SDK for OpenClaw AI entities."""

from nostrwalletconnect.client import NWCClient
from nostrwalletconnect.connection import NWCConnection

__version__ = "0.1.1"
__all__ = [
    "NWCClient",
    "NWCConnection",
]
