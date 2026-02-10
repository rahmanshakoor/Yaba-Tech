import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../test-utils';
import { Routes, Route } from 'react-router-dom';

// Mock all page components to avoid heavy rendering / API calls
vi.mock('../../src/pages/Dashboard', () => ({ default: () => <div>Dashboard Page</div> }));
vi.mock('../../src/pages/DefinitionsPage', () => ({ default: () => <div>Definitions Page</div> }));
vi.mock('../../src/pages/InventoryPage', () => ({ default: () => <div>Inventory Page</div> }));
vi.mock('../../src/pages/RecipesPage', () => ({ default: () => <div>Recipes Page</div> }));
vi.mock('../../src/pages/ProductionPage', () => ({ default: () => <div>Production Page</div> }));
vi.mock('../../src/pages/InvoicesPage', () => ({ default: () => <div>Invoices Page</div> }));

import Dashboard from '../../src/pages/Dashboard';
import DefinitionsPage from '../../src/pages/DefinitionsPage';
import InventoryPage from '../../src/pages/InventoryPage';
import RecipesPage from '../../src/pages/RecipesPage';
import ProductionPage from '../../src/pages/ProductionPage';
import InvoicesPage from '../../src/pages/InvoicesPage';

const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/definitions" element={<DefinitionsPage />} />
    <Route path="/inventory" element={<InventoryPage />} />
    <Route path="/recipes" element={<RecipesPage />} />
    <Route path="/production" element={<ProductionPage />} />
    <Route path="/invoices" element={<InvoicesPage />} />
  </Routes>
);

describe('App Routing', () => {
  it('renders the Dashboard on "/"', () => {
    renderWithProviders(<AppRoutes />);
    expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
  });

  it('renders Definitions page on "/definitions"', () => {
    renderWithProviders(<AppRoutes />, undefined, ['/definitions']);
    expect(screen.getByText('Definitions Page')).toBeInTheDocument();
  });

  it('renders Inventory page on "/inventory"', () => {
    renderWithProviders(<AppRoutes />, undefined, ['/inventory']);
    expect(screen.getByText('Inventory Page')).toBeInTheDocument();
  });

  it('renders Recipes page on "/recipes"', () => {
    renderWithProviders(<AppRoutes />, undefined, ['/recipes']);
    expect(screen.getByText('Recipes Page')).toBeInTheDocument();
  });

  it('renders Production page on "/production"', () => {
    renderWithProviders(<AppRoutes />, undefined, ['/production']);
    expect(screen.getByText('Production Page')).toBeInTheDocument();
  });

  it('renders Invoices page on "/invoices"', () => {
    renderWithProviders(<AppRoutes />, undefined, ['/invoices']);
    expect(screen.getByText('Invoices Page')).toBeInTheDocument();
  });
});
