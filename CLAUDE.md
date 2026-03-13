# CLAUDE.md — nwc.app.OC-python.src

## What This Is
Open-source Python SDK for OpenClaw AI entities to connect to Lightning wallets via Nostr Wallet Connect (NIP-47). Lets bots pay invoices, check balance, create invoices, and list transactions.

## Ecosystem Position
This SDK gives AI agents wallet access without custody. The human controls the wallet. The agent gets a scoped NWC connection string. Built on top of `nostrkey` for all Nostr crypto/relay primitives.

## Package Name
`nostrwalletconnect` on PyPI — `pip install nostrwalletconnect`

## Module Structure
- `nostrwalletconnect.connection` — parse `nostr+walletconnect://` URIs (NWCConnection dataclass)
- `nostrwalletconnect.client` — NWCClient async context manager, all NIP-47 methods
- `nostrwalletconnect.types` — response dataclasses (BalanceResponse, PayResponse, etc.)

## Key Design Decisions
- Depends on `nostrkey` — no duplication of crypto/relay code
- Async-first API (asyncio + websockets)
- NIP-44 encrypted communication (via nostrkey.crypto)
- Event kinds: 23194 (request), 23195 (response), 13194 (info)
- Type hints throughout, Python 3.10+
- MIT licensed, open source

## Conventions
- kebab-case for file names in docs/config, snake_case for Python modules
- Tests in `tests/` using pytest
- Examples in `examples/`
- ClawHub skill definition in `clawhub/` (SKILL.md + metadata.json)
- Keep `metadata.json` version in sync with `pyproject.toml`

## Related Repos
- `nostrkey.app.OC-python.src` — NostrKey identity SDK (dependency)
- `loginwithnostr.web.landingpage.src` — Landing page, `/openclaw` lists this skill
- `nostrkey.bizdocs.src` — Business docs (OpenClaw GTM)
