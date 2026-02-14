# YABA Frontend

React single-page application for the YABA Kitchen Management System. Provides an operator-facing UI for inventory, production, recipes, invoices, waste logging, and demand forecasting.

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | React 19 |
| Language | TypeScript 5.9 |
| Build Tool | Vite 7 |
| Styling | Tailwind CSS 4 |
| Routing | React Router DOM 7 |
| Server State | TanStack Query (React Query) 5 |
| HTTP Client | Axios |
| Icons | lucide-react |
| Testing | Vitest 4, React Testing Library, jsdom |
| Linting | ESLint 9, typescript-eslint |

---

## Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The app opens at `http://localhost:5173` by default. It expects the backend API at `http://localhost:8000`.

---

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start Vite dev server with hot-module replacement |
| `npm run build` | Type-check with `tsc` then build for production |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint across the project |
| `npm test` | Run the full Vitest test suite |
| `npm run test:watch` | Run tests in watch mode (re-runs on file changes) |

---

## Project Structure

```
frontend/
├── public/                  # Static assets
├── src/
│   ├── main.tsx             # React DOM entry point
│   ├── App.tsx              # Router configuration and layout shell
│   ├── index.css            # Global styles (Tailwind imports)
│   ├── pages/               # Route-level page components
│   │   ├── Dashboard.tsx
│   │   ├── DefinitionsPage.tsx
│   │   ├── InventoryPage.tsx
│   │   ├── InvoicesPage.tsx
│   │   ├── ProductionPage.tsx
│   │   └── RecipesPage.tsx
│   ├── components/
│   │   ├── common/          # Reusable UI primitives (Button, Input, DataTable, Modal, StatusBadge)
│   │   └── layout/          # App shell (Sidebar, TopBar, PageLayout)
│   ├── features/            # Feature-specific modules
│   │   ├── dashboard/       # DailyPrepList, DemandTrendWidget, forecast hooks
│   │   ├── inventory/       # InventoryTable, WasteModal, StockAdjustment
│   │   ├── invoices/        # InvoiceUploader, ManualInvoiceForm
│   │   ├── production/      # ProduceForm, DepleteForm, ProductionForm, ProductionLogTable
│   │   └── recipes/         # RecipeBuilder, RecipeList
│   ├── services/
│   │   └── api.ts           # Axios client (baseURL: http://localhost:8000)
│   ├── hooks/               # Shared React hooks
│   └── types/               # TypeScript interfaces and type definitions
├── tests/                   # Vitest test suite
│   └── pages/               # Page-level integration tests
├── index.html               # HTML entry point
├── vite.config.ts           # Vite + React + Tailwind configuration
├── tsconfig.json            # Base TypeScript config
├── tsconfig.app.json        # App-specific TS config
├── tsconfig.node.json       # Node/Vite TS config
├── eslint.config.js         # ESLint configuration
└── package.json             # Dependencies and scripts
```

---

## Routing

| Path | Page | Description |
|---|---|---|
| `/` | Dashboard | KPI cards, recent production logs, forecast widgets |
| `/definitions` | Definitions | Item master data CRUD (Raw, Prepped, Dish) |
| `/inventory` | Inventory | Stock summary by item, batch details, waste logging |
| `/recipes` | Recipes | Recipe builder and ingredient composition editor |
| `/production` | Production | Record production runs or stock depletions via toggle, stock checks, production history |
| `/invoices` | Invoices | Invoice list, manual entry, OCR image upload |

---

## Component Architecture

```
App.tsx
├── Sidebar               # Navigation links
├── TopBar                # Page header
└── <Routes>
    ├── Dashboard
    │   ├── KPI stat cards
    │   ├── RecentProductionLogs
    │   └── DemandTrendWidget
    ├── DefinitionsPage
    │   └── DataTable + Modal (create / edit items)
    ├── InventoryPage
    │   ├── InventoryTable (summary view)
    │   ├── Batch detail expansion
    │   └── WasteModal
    ├── RecipesPage
    │   ├── RecipeList
    │   └── RecipeBuilder
    ├── ProductionPage (produce / deplete toggle)
    │   ├── ProduceForm (recipe-based production)
    │   ├── DepleteForm (stock depletion for sales/POS)
    │   ├── IngredientBatchSelector
    │   └── ProductionLogTable
    └── InvoicesPage
        ├── Invoice list
        ├── ManualInvoiceForm
        └── InvoiceUploader (OCR)
```

### Key Patterns

- **TanStack Query** manages all server state — data fetching, caching, and mutation invalidation.
- **Feature modules** (`src/features/`) encapsulate domain-specific components and hooks, keeping pages thin.
- **Shared components** (`src/components/common/`) provide reusable primitives (DataTable, Modal, Button, Input, StatusBadge).
- **Layout components** (`src/components/layout/`) define the application shell (Sidebar, TopBar, PageLayout).

---

## Testing

```bash
# Full suite
npm test

# Watch mode
npm run test:watch

# Single file
npx vitest run tests/pages/RecipeBuilder.test.tsx
```

Tests use **Vitest** with **React Testing Library** and **jsdom** for DOM simulation.

See [TESTING.md](../TESTING.md) for the test file map, manual QA checklist, and CI/CD workflow.
