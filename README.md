# AI4SWEng FastAPI Demo Repository

A small but realistic **inventory and user management API** built with FastAPI. It is designed as a target codebase for AI4SWEng agent demonstrations:

| Agent | Typical focus on this repo |
|-------|---------------------------|
| **RepoAnalyzerAgent** | Module layout, auth flow, SQL usage, test gaps |
| **TestGeneratorAgent** | Missing coverage, edge cases, security regressions |
| **DebuggerAgent** | Failing behavior, null access, pagination anomalies |
| **PatchAgent** | Targeted fixes with minimal diffs |
| **HumanApproval** | Security-sensitive patches (auth, SQL) |
| **EvidenceReport** | Trace findings to file:line with reproduction steps |

The service is intentionally imperfect — suitable for find-and-fix workflows, not production deployment.

## Features

- **Authentication** — JWT login (`/api/v1/auth/login`, `/api/v1/auth/login/json`)
- **User management** — registration, profiles, admin search
- **Inventory** — categories, products, pagination, low-stock reporting
- **SQLite** persistence (swap to PostgreSQL via `DATABASE_URL`)
- **Unit tests** with pytest (partial coverage by design)

## Quick start

### Prerequisites

- Python 3.11+
- pip

### Install

```bash
cd ai4sweng-fastapi-demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn app.main:app --reload --port 8080
```

- Health: http://localhost:8080/health
- OpenAPI docs: http://localhost:8080/docs

### Run tests

```bash
pytest tests/ -v
```

## Default demo data

On first startup the API creates an empty database. Tests seed:

| Account | Password | Role |
|---------|----------|------|
| `admin` | `adminpass123` | admin |
| `alice` | `alicepass123` | user |

Sample products: `SKU-001` (low stock), `SKU-002`, `SKU-003` under category **Electronics**.

### Example: login and list products

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alicepass123"}' | jq -r .access_token)

curl -s "http://localhost:8080/api/v1/inventory/products?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Project layout

```
ai4sweng-fastapi-demo/
├── README.md
├── requirements.txt
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Settings (env / .env)
│   ├── database.py          # SQLAlchemy engine + sessions
│   ├── dependencies.py      # JWT auth dependencies
│   ├── logging_config.py    # Logging setup
│   ├── auth/                # Login, token issuance, password reset
│   ├── users/               # Registration, profiles, search
│   └── inventory/           # Categories, products, stock
└── tests/
    ├── conftest.py          # In-memory DB fixtures
    ├── test_auth.py
    ├── test_users.py
    └── test_inventory.py
```

**19 application source files** under `app/` (within the 15–20 target range).

## API overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | — | Liveness check |
| POST | `/api/v1/auth/login` | — | OAuth2 form login |
| POST | `/api/v1/auth/login/json` | — | JSON login |
| POST | `/api/v1/auth/reset-password` | admin | Password reset |
| POST | `/api/v1/users` | — | Register user |
| GET | `/api/v1/users/me` | user | Current user |
| GET | `/api/v1/users` | admin | List users |
| GET | `/api/v1/users/search?q=` | admin | Search by username |
| GET | `/api/v1/users/{id}/profile` | — | User profile |
| PUT | `/api/v1/users/{id}/profile` | user/admin | Update profile |
| POST | `/api/v1/inventory/categories` | admin | Create category |
| GET | `/api/v1/inventory/categories` | user | List categories |
| POST | `/api/v1/inventory/products` | admin | Create product |
| GET | `/api/v1/inventory/products` | user | Paginated list |
| GET | `/api/v1/inventory/products/low-stock` | user | Low-stock report |
| GET | `/api/v1/inventory/products/{id}` | user | Product detail |
| PATCH | `/api/v1/inventory/products/{id}` | admin | Update product |
| DELETE | `/api/v1/inventory/products/{id}` | admin | Delete product |

## Configuration

Environment variables (optional `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./inventory_demo.db` | SQLAlchemy URL |
| `JWT_SECRET` | `demo-secret-change-in-production` | Signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token TTL |
| `DEFAULT_PAGE_SIZE` | `10` | Inventory page size |

## Demonstration scenarios

Suggested exercises for agent pipelines:

1. **Static analysis** — map auth → users → inventory dependencies; list raw SQL usage.
2. **Test generation** — add tests for admin-only endpoints and error paths.
3. **Debug session** — reproduce pagination and low-stock anomalies from failing assertions.
4. **Security review** — inspect login logging and search query construction.
5. **Performance pass** — profile product listing with many SKUs.
6. **Patch + approval** — propose minimal fix; human approves before merge.

## Development

```bash
# Format / lint (optional tooling not bundled)
pytest tests/ -v --tb=short

# Run on alternate port
uvicorn app.main:app --port 9090
```

## License

Demonstration codebase for AI4SWEng coursework and agent evaluation. Use freely in workshops.
