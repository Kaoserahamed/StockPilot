# StockPilot — Inventory & POS SaaS

**All-in-one point-of-sale, inventory, finance and AI insights platform for small retail businesses.**

StockPilot helps busy retail counters run their whole operation from one calm workspace — a fast POS terminal with invoice/PDF generation, live inventory with low-stock alerts, purchase and supplier tracking, profit & finance dashboards, report exports (CSV / Excel / PDF) and an AI assistant that forecasts demand, flags anomalies and recommends reorders.

---

## Table of Contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Repository layout](#repository-layout)
4. [How to run locally (Windows, no Docker)](#run-locally)
5. [Run the tests](#run-the-tests)
6. [Deploy (Docker + Postgres)](#deploy)
7. [API overview](#api-overview)

---

## Features

### 🔐 Onboarding & access
- **Registration & JWT login** — owner signs up with name, email/phone, password and shop profile.
- **Password reset** — request a reset code, then set a new password.
- **Role-based access (RBAC)** — `Owner`, `Manager` and `Cashier` roles, enforced on every endpoint.
- **Team management** — create employee accounts, activate/deactivate, re-assign roles, reset passwords, remove members.

### 🛍️ POS & sales
- **POS terminal** — product search by name / SKU / barcode, add to cart, discount & tax, checkout in seconds.
- **Sales history** — list, filter and drill into past sales.
- **Invoices** — auto-numbered per business, printable, downloadable as **PDF**.
- **Returns** — full or partial item returns that restock inventory and correct customer balances.
- **Customers** — records with phone/email/address, credit support, outstanding balances and per-customer sales history.

### 📦 Inventory & purchasing
- **Catalog** — categories + products (SKU, barcode, brand, unit, prices, min-stock) with duplicate SKU/barcode protection.
- **Live stock** — quantity-on-hand is updated by every purchase, sale and return.
- **Stock health** — low-stock and out-of-stock flags, min-stock defaults, inventory overview with filters.
- **Adjustments** — manual stock corrections with a mandatory reason and full transaction history.
- **Purchases** — supplier orders, auto-calculated totals, partial/full payments, supplier outstanding balances and purchase history.

### 💰 Finance & analytics
- **Dashboard** — revenue, gross/net profit, expenses, inventory value, sales trend chart, bestsellers and stock alerts in one view.
- **Finance** — revenue, COGS and profit for today / 7 days / 30 days / 12 months / all time or custom date ranges.
- **Reports** — sales, inventory, purchases, expenses and profit; export as **CSV, Excel or PDF**.
- **Expenses** — categorized operational expenses (rent, salary, electricity, transport, maintenance, …).

### 🤖 AI assistant (deterministic analytics + optional Gemini polish)
- **Q&A** — natural-language questions answered from your live business data.
- **Insights** — automatically spotted sales changes, expense warnings and demand shifts.
- **Forecasts** — 30+ day demand predictions per product from real sales velocity.
- **Reorder recommendations** — `predicted demand + min-stock − on-hand` per product.
- **Anomaly detection** — z-score outliers on daily revenue and abnormally large sales.
- **Recommendation history** — mark insights as reviewed / acted upon.

### 🏢 Workspace admin & SaaS
- **Multi-tenancy** — every record is scoped to a business; cross-business access is blocked.
- **Settings** — business profile, currency, tax rate, invoice format, default min stock.
- **Audit log** — append-only history of who changed what and when.
- **Subscription / billing** — free / basic / pro plans with product & team limits and usage meters.

---

## Tech stack

| Layer          | Technology                                                        |
| -------------- | ----------------------------------------------------------------- |
| Frontend       | **Next.js 14 (App Router) + TypeScript**                          |
| Styling        | **Tailwind CSS** (custom shadcn-style component set)              |
| Data fetching  | **TanStack Query (React Query)** + Axios                          |
| Charts         | **Recharts**                                                      |
| Backend        | **FastAPI (Python 3.11)**                                         |
| ORM            | **SQLAlchemy 2.x**                                                |
| Database       | **MySQL 8** locally · **PostgreSQL 16** for deployment            |
| Validation     | **Pydantic v2**                                                   |
| Authentication | **JWT (python-jose) + bcrypt**                                    |
| AI             | In-app deterministic analytics + optional **Gemini API** polish   |
| Exports        | **ReportLab** (PDF) · **OpenPyXL** (Excel) · stdlib `csv`         |
| File storage   | Local filesystem (`backend/uploads`)                              |
| Testing        | **Pytest** + FastAPI TestClient (SQLite in-memory)                |

> App code is database-dialect agnostic via SQLAlchemy — switching MySQL → Postgres is only a `DATABASE_URL` + driver change.

---

## Repository layout

```
B/
├── backend/                 # FastAPI service
│   ├── app/
│   │   ├── api/v1/          # routers: auth, products, sales, finance, ai, ...
│   │   ├── core/            # config, security (JWT), dependencies (RBAC ctx)
│   │   ├── db/              # engine/session, model registration
│   │   ├── models/          # SQLAlchemy models (sales, products, finance, ...)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # finance, inventory, invoice, AI logic
│   │   └── main.py          # FastAPI app + router registration
│   ├── tests/               # pytest suite (SQLite in-memory — no MySQL needed)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # Next.js 14 app
│   ├── app/                 # routes: login, dashboard, pos, products, ...
│   ├── components/          # Shell (sidebar) + UI primitives
│   └── lib/                 # axios api client + auth context
├── docker-compose.yml       # OPTIONAL legacy MySQL-in-Docker helper (not for local run)
├── docker-compose.prod.yml  # DEPLOY stack: Postgres + API
└── ProjectDetails.md        # functional requirements (FR-1..FR-37)
```

---

<a id="run-locally"></a>
## How to run locally (Windows, no Docker)

Local setup uses **native MySQL** — no Docker, no Postgres install needed.

### 0) Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MySQL 8 running locally** with a database named `pos_saas`
  (default dev connection: `mysql+pymysql://root:root@localhost:3306/pos_saas`)

### 1) Backend (FastAPI)

```powershell
cd E:\B\backend

# create + fill the env file (or copy .env.example)
#   DATABASE_URL=mysql+pymysql://root:root@localhost:3306/pos_saas
#   SECRET_KEY=change-me-to-a-long-random-secret-in-production
pip install -r requirements.txt

# (optional) create tables now — they are also auto-created on server startup
python -c "from app.db.base import Base; import app.models; from app.db.session import engine; Base.metadata.create_all(bind=engine); print('tables ok')"

# start the API
uvicorn app.main:app --reload --port 8000
```

- Swagger docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

On startup the app: creates any missing tables, creates any missing query
indexes (non-destructive), and serves `/api/v1/...`.

### 2) Frontend (Next.js)

```powershell
cd E:\B\frontend
npm install

# frontend\.env.local must contain:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open **<http://localhost:3000>** → register an owner account (creates your
business automatically) → you land on the dashboard.

### 3) Try the end-to-end flow

1. **Register** an owner account.
2. **Categories → Products** — add a couple of products with prices.
3. **Purchases** — buy stock from a supplier (stock increases automatically).
4. **POS Terminal** — search a product, add to cart, checkout (stock reduces, invoice generated).
5. **Dashboard / Finance / Reports** — live KPIs, trends and CSV/Excel/PDF exports.
6. **AI Assistant** — ask "which products should I reorder?" for insights, forecasts and reorder suggestions.

---

<a id="run-the-tests"></a>
## Run the tests

The suite uses **SQLite in-memory** — MySQL does not need to be running.

```powershell
cd E:\B\backend
python -m pytest tests/ -v
```

---

<a id="deploy"></a>
## Deploy (Docker + Postgres — NOT for local use)

On a server / VPS:

```powershell
$env:SECRET_KEY="<long-random-secret>"
docker compose -f docker-compose.prod.yml up --build -d
```

This starts **postgres:16-alpine** + the API container (frontend can be built
separately or served by any static host / reverse proxy).

**PaaS alternative (Render / Railway / Supabase / Neon):** create a managed
Postgres and set environment variables:

```
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
SECRET_KEY=<long-random-secret>
```

(`postgres://...` short URLs are also accepted — they are auto-normalized in
`app/db/session.py`.)

---

<a id="api-overview"></a>
## API overview

Base URL: **`/api/v1/...`** — interactive docs at `/docs`.

| Group        | Highlights                                                                    |
| ------------ | ------------------------------------------------------------------------------ |
| `auth`       | register, login (JWT), logout, me, forgot/reset password                        |
| `businesses` | my business, update profile, logo upload                                        |
| `employees`  | list/create team members, roles, activate/deactivate, reset password, remove    |
| `categories` `products` | CRUD, search by name/SKU/barcode/brand, images, activate/deactivate  |
| `suppliers` `customers` | CRUD + purchase/sales history + outstanding balances                 |
| `inventory`  | overview + filters, low-stock/out-of-stock, transactions, manual adjustments    |
| `purchases`  | create multi-item orders, pay, cancel (restock)                                 |
| `sales`      | checkout (POS), history, detail, cancel; invoice view + PDF                     |
| `returns`    | full/partial returns (restock + balance correction)                             |
| `expenses`   | categorized operational expenses                                                |
| `finance`    | revenue / COGS / profit by preset or custom range                               |
| `analytics`  | dashboard KPIs, product/customer/supplier performance                           |
| `reports`    | sales/inventory/purchases/expenses/profit + `format=csv\|excel\|pdf`            |
| `settings`   | business config: currency, tax, invoice format, min-stock default               |
| `subscription` | plan status, usage vs limits, plan change                                     |
| `ai`         | chat Q&A, insights, forecast, reorder recommendations, anomalies, history       |
| `audit-logs` | append-only activity log (Owner/Manager)                                        |

**Auth:** send `Authorization: Bearer <JWT>` on every request. Multi-business
users can pass `X-Business-Id: <id>` to select the active business context.
