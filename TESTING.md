# TESTING.md — YABA Kitchen Management System

This guide explains how to run tests, seed demo data, and perform manual QA for the YABA system.

---

## 1. Backend Testing (Python / FastAPI)

### Prerequisites

```bash
cd backend
pip install -r requirements.txt
# Key test dependencies included in requirements.txt:
#   pytest, pytest-asyncio, httpx, aiosqlite
```

### Running Tests

```bash
# Full test suite
cd backend
pytest

# Verbose output
pytest -v

# Single test file
pytest tests/test_inventory_service.py

# Single test function
pytest tests/test_costing.py::test_pizza_rollup_cost

# Coverage report (install pytest-cov first)
pip install pytest-cov
pytest --cov=src

# Coverage with HTML report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in a browser
```

### Test File Map

| Source File | Test File |
|---|---|
| `src/services/cost_service.py` | `tests/test_costing.py` |
| `src/services/forecasting_service.py` | `tests/test_forecasting.py` |
| `src/services/inventory_service.py` | `tests/test_inventory_service.py` |
| `src/services/recipe_service.py` | `tests/test_recipe_service.py` |
| `src/services/ocr_service.py` | `tests/test_ocr_service.py` |
| `src/services/unit_conversion.py` | `tests/test_unit_conversion.py` |
| `src/routers/production.py` | `tests/test_production.py` |
| `src/routers/ingestion.py` | `tests/test_ingestion.py` |
| `src/models.py` | `tests/test_models.py` |
| Waste & Revert workflows | `tests/test_exceptions.py` |

---

## 2. Frontend Testing (React / Vitest)

### Prerequisites

```bash
cd frontend
npm install
```

### Running Tests

```bash
# Full test suite
npm test

# Watch mode (re-runs on file change)
npm run test:watch

# Single test file
npx vitest run tests/pages/RecipeBuilder.test.tsx
```

### Test File Map

| Component / Page | Test File |
|---|---|
| App routing | `tests/pages/App.test.tsx` |
| RecipeBuilder | `tests/pages/RecipeBuilder.test.tsx` |
| InventoryPage | `tests/pages/InventoryPage.test.tsx` |
| ProductionPage | `tests/pages/ProductionPage.test.tsx` |
| DefinitionsPage | `tests/pages/DefinitionsPage.test.tsx` |
| DashboardForecast | `tests/pages/DashboardForecast.test.tsx` |
| InvoicesPage | `tests/pages/InvoicesPage.test.tsx` |

---

## 3. Seeding Data for Manual Testing

The seed script populates a local SQLite database with 30 days of realistic "Italian Bistro" data.

```bash
cd backend
python scripts/seed_data.py
```

This creates:
- **Items**: 00 Flour, San Marzano Tomatoes, Mozzarella Cheese, Fresh Basil, Pizza Dough, Pizza Sauce, Margherita Pizza, Marinara Pizza.
- **Invoices**: One initial purchase invoice dated 30 days ago.
- **Production history**: 29 days of daily pizza production.
- **Edge cases**: Low-stock basil, expiring mozzarella batch, waste log entry, and a pending (draft) invoice.

### Manual Verification Checklist

After seeding, start the backend (`uvicorn src.main:app --reload`) and frontend (`npm run dev`) and verify:

1. **Dashboard** — KPI cards show non-zero values for Low Stock Items, Today's Production Cost, Pending Invoices, and Weekly Waste Value.
2. **Definitions** — All 8 items appear. Click a Dish item to see its recipe composition.
3. **Inventory**
   - Summary table lists items with stock > 0 and their total values.
   - Click "Log Waste" on a batch → enter a quantity → verify stock decreases.
4. **Recipes** — Select "Margherita Pizza" → verify the recipe shows Dough, Sauce, Cheese, and Basil as ingredients.
5. **Production** — Select a Dish → verify "Stock Check" reflects current ingredient availability. Produce 1 unit → verify input ingredient stocks decrease and a new output batch appears.
6. **Invoices** — The list shows the seed invoice. Click "Add Invoice" → fill in supplier and line items → submit → verify a new invoice appears and inventory increases.
7. **Forecasting** — The dashboard forecast section displays reorder recommendations for items with low projected stock.

---

## 4. CI/CD Configuration

Below is a sample GitHub Actions workflow that runs both backend and frontend tests on every pull request.

Save this as `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pip install pytest-cov
      - run: pytest --cov=src -v

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm test
```
