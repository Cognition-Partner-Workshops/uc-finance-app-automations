# TraderX — Legacy Trading Platform

A multi-tenant trading platform built as a Python/FastAPI monolith. Supports account management, trade submission, position tracking, and real-time updates via Socket.io. Uses SQLite for storage with 3 demo tenants (`acme_corp`, `globex_inc`, `initech`).

[![CI](https://github.com/mbatchelor81/traderXCognitiondemos/actions/workflows/ci.yml/badge.svg)](https://github.com/mbatchelor81/traderXCognitiondemos/actions/workflows/ci.yml)

---

## Prerequisites

- **Python 3.11+**
- **Node 18+**
- **npm**

---

## Quick Start

### 1. Start the backend

```bash
cd traderx-monolith
pip install -r requirements.txt
python run.py
```

The API will be available at `http://localhost:8000`.

### 2. Start the frontend

```bash
cd web-front-end/react
npm install
npm start
```

The UI will be available at `http://localhost:3000`.

### 3. Open the app

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

---

## Sentry Demo (error monitoring)

The backend reports uncaught server errors (HTTP 500s) to [Sentry](https://sentry.io) **only when a `SENTRY_DSN` is configured**. Without it, `sentry_sdk.init()` is skipped and nothing is sent — the errors still occur, but no alerts fire.

### 1. Get a DSN

In Sentry, open **Settings → Projects → _your project_ → Client Keys (DSN)** and copy the DSN. It looks like:

```
https://<publicKey>@o<org>.ingest.sentry.io/<projectId>
```

If you don't have a project yet, create one with platform **Python / FastAPI**.

### 2. Configure it locally

```bash
cd traderx-monolith
cp .env.example .env
# edit .env and set SENTRY_DSN=...
python run.py
```

The backend auto-loads `traderx-monolith/.env` on startup (via `python-dotenv`). Alternatively, export it in your shell before running:

```bash
export SENTRY_DSN="https://<publicKey>@o<org>.ingest.sentry.io/<projectId>"
python run.py
```

> `.env` is git-ignored — never commit your DSN.

### 3. Verify

Trigger the built-in test error and confirm it appears in Sentry within a few seconds:

```bash
curl http://localhost:8000/sentry-debug
```

Any uncaught 500 from the app (e.g. the demo flows in the UI) will now show up as a Sentry issue.

> Scope: this instruments the **backend** only (where the errors are raised). The React frontend is not wired to Sentry.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/account/` | List all accounts for the current tenant |
| `POST` | `/account/` | Create a new account |
| `PUT` | `/account/` | Update an existing account |
| `GET` | `/account/{account_id}` | Get account by ID with portfolio summary |
| `GET` | `/accountuser/` | List all account users |
| `POST` | `/accountuser/` | Create a new account user |
| `PUT` | `/accountuser/` | Update an account user |
| `POST` | `/trade/` | Submit a new trade order |
| `GET` | `/trades/` | List all trades for the current tenant |
| `GET` | `/trades/{account_id}` | List trades for a specific account |
| `GET` | `/positions/` | List all positions for the current tenant |
| `GET` | `/positions/{account_id}` | List positions for a specific account |
| `GET` | `/stocks/` | List all S&P 500 stocks |
| `GET` | `/stocks/{ticker}` | Get stock by ticker symbol |
| `GET` | `/people/GetPerson` | Get a person by LogonId or EmployeeId |
| `GET` | `/people/GetMatchingPeople` | Search for people matching text |
| `GET` | `/people/ValidatePerson` | Validate that a person exists |
| `GET` | `/health` | Health check |

---

## Multi-Tenant

TraderX supports multiple tenants via the `X-Tenant-ID` HTTP header. If the header is not provided, the default tenant (`acme_corp`) is used.

### Available Tenants

| Tenant ID | Description |
|---|---|
| `acme_corp` | 2 accounts, 8 trades, 7 positions |
| `globex_inc` | 2 accounts, 5 trades, 5 positions |
| `initech` | 3 accounts, 8 trades, 7 positions |

### Example

```bash
# List accounts for the default tenant (acme_corp)
curl http://localhost:8000/account/

# List accounts for a specific tenant
curl -H "X-Tenant-ID: globex_inc" http://localhost:8000/account/
```

---

## Architecture

This is a legacy monolithic application with known technical debt. See the following documents for details:

- **[LEGACY_ARCHITECTURE.md](LEGACY_ARCHITECTURE.md)** — Current system architecture, database schema, module coupling, and known anti-patterns
- **[TARGET_ARCHITECTURE_CONSTRAINTS.md](TARGET_ARCHITECTURE_CONSTRAINTS.md)** — Target state requirements and constraints for a future migration to microservices

---

## License

Copyright 2023 UBS, FINOS, Morgan Stanley

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)
