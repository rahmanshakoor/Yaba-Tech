# YABA — Yet Another Back-of-house App

A full-stack **Kitchen Management System** built for food-service operations. YABA tracks inventory at the batch level, manages recipe-based production, logs waste, processes supplier invoices, and forecasts demand using statistical models.

---

## Features

| Module | Capabilities |
|---|---|
| **Inventory** | Batch-level stock tracking (FIFO), expiration dates, unit cost per batch, stock adjustments |
| **Production** | Recipe-based ingredient deduction, production logging with full traceability, revert support |
| **Recipes** | Hierarchical composition (Raw → Prepped → Dish), cost roll-up calculations |
| **Costing** | Automatic recipe cost from ingredient costs, waste cost tracking, daily aggregation |
| **Waste** | Log waste by reason (Spoiled, Dropped, Burned, Theft), cost-loss calculation |
| **Invoices** | Manual invoice entry, OCR-based image upload, auto-inventory creation |
| **Forecasting** | ARIMA / SARIMA demand prediction, 7–90 day horizons, reorder recommendations |
| **Dashboard** | KPI cards, recent production logs, forecast widgets |

---

## Architecture

```
┌──────────────┐        HTTP / JSON        ┌──────────────────┐
│   Frontend   │  ◄──────────────────────►  │     Backend      │
│  React 19    │                            │  FastAPI 0.104+  │
│  TypeScript  │                            │  Python 3.12     │
│  Vite        │                            │  SQLAlchemy 2    │
│  Tailwind    │                            │  SQLite (async)  │
└──────────────┘                            └──────────────────┘
```

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4, TanStack Query, Axios, React Router 7 |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic 2 |
| **ORM / DB** | SQLAlchemy 2 (async) + aiosqlite, SQLite |
| **Analytics** | statsmodels (ARIMA/SARIMA), NumPy |
| **Testing** | pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend) |

---

## Project Structure

```
Yaba-Tech/
├── backend/                 # FastAPI server
│   ├── src/
│   │   ├── main.py          # Application entry point
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── database.py      # Async database engine
│   │   ├── routers/         # API endpoint routers
│   │   └── services/        # Business logic layer
│   ├── tests/               # pytest test suite
│   ├── scripts/             # Seed data scripts
│   └── requirements.txt     # Python dependencies
├── frontend/                # React SPA
│   ├── src/
│   │   ├── pages/           # Route-level page components
│   │   ├── components/      # Shared UI components
│   │   ├── features/        # Feature-specific modules
│   │   ├── services/        # Axios API client
│   │   ├── types/           # TypeScript interfaces
│   │   └── App.tsx          # Router and layout shell
│   ├── tests/               # Vitest test suite
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite configuration
├── TESTING.md               # Testing and QA guide
└── README.md                # ← You are here
```

---

## Quick Start

### Prerequisites

- **Python** 3.12+
- **Node.js** 20+
- **npm** 10+

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app opens at `http://localhost:5173` by default.

### 3. Seed Demo Data (optional)

```bash
cd backend
python scripts/seed_data.py
```

Populates the database with 30 days of Italian-bistro sample data (items, invoices, production history, waste logs).

---

## Testing

See [TESTING.md](TESTING.md) for the full testing guide, including manual QA checklists and CI/CD configuration.

```bash
# Backend
cd backend && pytest -v

# Frontend
cd frontend && npm test
```

---

## Documentation

| Document | Description |
|---|---|
| [Backend README](backend/README.md) | Setup, API reference, database schema, and services |
| [Frontend README](frontend/README.md) | Setup, component architecture, and build scripts |
| [TESTING.md](TESTING.md) | Test commands, seed data, manual QA, and CI/CD workflow |

---

## License

This project is for internal use. See repository settings for access and licensing details.
