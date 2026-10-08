# Legacy Architecture — TraderX Monolith

This document describes the current architecture of the TraderX trading platform. TraderX is a **legacy monolithic application** built as a single Python/FastAPI process serving all trading functionality. It was consolidated from a distributed microservices architecture into a single deployable unit and carries significant technical debt by design.

---

## System Overview

TraderX is a single Python/FastAPI monolith that serves all trading functionality through one process:

- **Account management** — create, update, and query trading accounts and account users
- **Trade submission and processing** — submit trade orders, validate, process, and settle trades synchronously
- **Position tracking** — maintain and query net holdings per account and security
- **Reference data** — S&P 500 stock ticker lookup from a CSV file loaded into memory
- **People directory** — user/person lookup from a JSON file loaded into memory
- **Real-time updates** — Socket.io server embedded in the same ASGI process for pushing trade and position updates to connected frontends

The backend runs on **uvicorn** (ASGI) at port `8000` by default. The frontend is a separate React application served on port `3000`.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                 │
│                     (React UI :3000)                            │
└──────────┬──────────────────────────────────┬───────────────────┘
           │ HTTP (REST API)                  │ WebSocket
           ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Monolith (:8000)                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  /account/*   │  │  /trade/     │  │  /positions/*         │  │
│  │  /accountuser/│  │  /trades/*   │  │                       │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘  │
│         │                 │                       │              │
│  ┌──────┴───────┐  ┌──────┴───────┐              │              │
│  │ account_     │◄►│ trade_       │──────────────┘              │
│  │ service.py   │  │ processor.py │ (cross-domain queries)      │
│  └──────────────┘  │ (god service)│                             │
│                    │ 848 lines    │                             │
│  ┌──────────────┐  └──────┬───────┘  ┌───────────────────────┐  │
│  │ /stocks/*    │         │          │ Socket.io Server       │  │
│  │ /people/*    │         ├─────────►│ (embedded in process)  │  │
│  │ (ref data +  │         │          │ real-time push         │  │
│  │  people svc) │         │          └───────────────────────┘  │
│  └──────────────┘         │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy ORM + SQLite                      │   │
│  │  ┌──────────┐ ┌──────────────┐ ┌────────┐ ┌───────────┐ │   │
│  │  │ accounts │ │ account_users│ │ trades │ │ positions │ │   │
│  │  └──────────┘ └──────────────┘ └────────┘ └───────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Global Config (config.py)                    │   │
│  │  Mutable runtime state, business rules, env vars         │   │
│  │  Imported via `from app.config import *` everywhere      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

```mermaid
graph TD
    Browser["Browser (React UI :3000)"]
    Monolith["FastAPI Monolith (:8000)"]
    SQLite["SQLite Database (traderx.db)"]
    SocketIO["Socket.io (embedded)"]

    Browser -->|"REST API (HTTP)"| Monolith
    Browser <-->|"WebSocket"| SocketIO
    Monolith --> SQLite
    Monolith --> SocketIO
    SocketIO -->|"trade & position updates"| Browser
```

---

## Single Shared Database

The application uses a **single SQLite database** (`traderx.db`) accessed through SQLAlchemy ORM. All domains (accounts, trades, positions) share the same database file and the same SQLAlchemy session factory.

### Tables

| Table | Primary Key |
|---|---|
| `accounts` | `id` (auto-increment) |
| `account_users` | composite (`account_id`, `username`) |
| `trades` | `id` (auto-increment) |
| `positions` | composite (`account_id`, `security`) |

### Business Rule Configuration

Application-wide business rules — `ALLOWED_TRADE_SIDES`, `AUTO_SETTLE_TRADES` — are defined as constants in `config.py` next to environment variables and mutable runtime state, and are picked up by the service layer through the wildcard `from app.config import *` import. A demo data set is seeded on first start.

---

## Tight Coupling Between Modules

### Cross-Domain Queries

The `trade_processor.py` god service directly queries account tables to validate trades:

- `validate_account_exists()` — queries the `accounts` table directly instead of calling account_service
- `validate_account_has_users()` — queries the `account_users` table directly
- `get_account_portfolio_summary()` — joins data from `accounts`, `trades`, and `positions` tables in a single cross-domain aggregation

### Circular Dependencies

`trade_processor.py` and `account_service.py` have a circular dependency:

- `trade_processor` imports `Account` and `AccountUser` models for cross-domain queries
- `account_service` imports `count_trades_for_account` from `trade_processor` (via lazy import to avoid import-time failure)

### Inconsistent Service Layer Usage

Some route handlers use the service layer, others bypass it with inline SQLAlchemy queries:

- `GET /trades/` uses a raw inline query (bypasses `trade_processor.get_all_trades()`)
- `GET /trades/{account_id}` uses the service layer (`trade_processor.get_trades_for_account()`)
- `GET /positions/*` endpoints use raw inline queries (bypasses trade_processor position functions)
- `GET /account/{account_id}` directly queries the positions table for portfolio summary

---

## God Service: `trade_processor.py`

The `trade_processor.py` module is **848 lines** and handles nearly all business logic:

| Responsibility | Functions |
|---|---|
| **Trade validation** | `validate_trade_request()`, `validate_account_exists()`, `validate_account_has_users()`, `validate_security_exists()` |
| **Trade processing** | `process_trade()` — the main orchestration function |
| **Trade state machine** | `can_transition()`, `transition_trade_state()` |
| **Position management** | `update_position()`, `get_current_position_quantity()`, `get_positions_for_account()`, `get_all_positions()` |
| **Socket.io publishing** | `publish_trade_update()`, `publish_position_update()`, `publish_trade_and_position()` |
| **Reporting/aggregation** | `get_account_portfolio_summary()`, `get_trade_volume_by_date()`, `get_top_traders()`, `get_position_concentration()` |
| **Business rules** | Allowed-side check in `validate_trade_request()` (`ALLOWED_TRADE_SIDES`) and auto-settle in `process_trade()` (`AUTO_SETTLE_TRADES`), both read from `config.py` |
| **Maintenance operations** | `settle_pending_trades()`, `cancel_stale_trades()`, `recalculate_positions()` |
| **Audit/history** | `get_recent_trades_audit()`, `get_trade_history()` |
| **Cross-domain helpers** | `get_account_details_for_trade()`, `validate_user_can_trade()`, `get_account_display_name()` |

---

## No Containerization

There are no Dockerfiles, no `docker-compose.yml` for the monolith, and no container build pipeline. The application runs directly on the host machine using Python and Node.js runtimes.

---

## Manual Deployment

Deployment is handled via `deploy.sh`, a shell script that:

1. Installs Python dependencies with `pip install`
2. Runs database seeding
3. Starts the backend with `python run.py`
4. Installs frontend dependencies and builds the React app
5. Serves the frontend with `npx serve`

There is no blue-green deployment, no rollback mechanism, and no health check verification in the deployment process.

---

## No CI/CD Pipeline

There are no GitHub Actions workflows, no automated test pipeline, no linting checks, and no automated deployment triggers for the monolith. All testing and deployment is manual.

---

## No Authentication or Authorization

| Layer | Protection |
|---|---|
| **Runtime** | None — a single process serves every request |
| **Database** | None — single SQLite file, all tables reachable from every request |
| **Configuration** | None — shared `config.py` with global mutable state |
| **Network** | None — single port, single process, no TLS |
| **Secrets** | None — plain environment variables read at import time |

There is no authentication, no authorization, and no request-level identity. Any client that can reach port `8000` can read and modify every account, trade, and position.

---

## Known Technical Debt

The following anti-patterns are **intentional** and present in the codebase by design:

### 1. Global Mutable Configuration (`config.py`)

- Every module imports config via `from app.config import *`
- `_runtime_state` dict is mutated from multiple modules (`total_trades_processed`, `last_trade_timestamp`, etc.)
- Business-rule constants live in the same namespace as environment settings and runtime counters

### 2. Inconsistent Service Layer Usage

- Some endpoints use `account_service` and `trade_processor` functions
- Other endpoints issue raw SQLAlchemy queries inline in route handlers
- No consistent pattern for when to use vs. bypass the service layer

### 3. Business Logic Mixed with Database Access

- `trade_processor.py` combines validation logic, state transitions, position calculations, Socket.io publishing, reporting queries, and audit logging in a single module
- No separation between domain logic and persistence layer
- Trade state machine, position arithmetic, and database operations are interleaved in `process_trade()`

### 4. Circular Dependencies

- `trade_processor.py` imports models used by `account_service.py`
- `account_service.py` lazily imports `count_trades_for_account` from `trade_processor.py`
- Resolved at runtime but creates fragile import ordering requirements

### 5. Business Rules in Config

- `ALLOWED_TRADE_SIDES`, `AUTO_SETTLE_TRADES` are defined as constants in `config.py`
- Business rules are coupled to configuration rather than being encapsulated in domain logic
- Changing a rule requires modifying the config module and restarting the process

### 6. No Error Boundaries

- Socket.io publish failures are caught but silently logged
- Database errors in seeding propagate as unhandled exceptions
- No circuit breaker, retry logic, or graceful degradation

### 7. SQLite as Production Database

- SQLite is a single-writer, file-based database not designed for concurrent production workloads
- No connection pooling, no read replicas, no backup strategy
