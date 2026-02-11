import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test-utils';
import InventoryPage from '../../src/pages/InventoryPage';

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url === '/items/') {
        return Promise.resolve({
          data: [
            { item_id: 1, name: 'Tomato', unit: 'kg', type: 'Raw', shelf_life_days: 7, is_archived: false },
            { item_id: 2, name: 'Prepped Sauce', unit: 'liters', type: 'Prepped', shelf_life_days: 3, is_archived: false },
            { item_id: 3, name: 'Lasagna', unit: 'portions', type: 'Dish', shelf_life_days: 2, is_archived: false },
          ]
        });
      }
      if (url === '/inventory/batches') {
        return Promise.resolve({
          data: [
            { batch_id: 101, item_id: 1, quantity_initial: 10, quantity_current: 8, expiration_date: '2026-03-01' },
            { batch_id: 102, item_id: 2, quantity_initial: 5, quantity_current: 3, expiration_date: '2026-02-15' },
            { batch_id: 103, item_id: 3, quantity_initial: 20, quantity_current: 15, expiration_date: '2026-02-20' },
          ]
        });
      }
      return Promise.resolve({ data: [] });
    }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

describe('InventoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows all batches by default', async () => {
    renderWithProviders(<InventoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Tomato')).toBeInTheDocument();
    });
    expect(screen.getByText('Prepped Sauce')).toBeInTheDocument();
  });

  it('filters to show only Raw items when Raw filter is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<InventoryPage />);

    await waitFor(() => {
      expect(screen.getByText('Tomato')).toBeInTheDocument();
    });

    const rawButton = screen.getByRole('button', { name: 'Raw' });
    await user.click(rawButton);

    expect(screen.getByText('Tomato')).toBeInTheDocument();
    expect(screen.queryByText('Prepped Sauce')).not.toBeInTheDocument();
  });

  it('filters to show only Prepped items when Prepped filter is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<InventoryPage />);

    await waitFor(() => {
      expect(screen.getByText('Prepped Sauce')).toBeInTheDocument();
    });

    const preppedButton = screen.getByRole('button', { name: 'Prepped' });
    await user.click(preppedButton);

    expect(screen.queryByText('Tomato')).not.toBeInTheDocument();
    expect(screen.getByText('Prepped Sauce')).toBeInTheDocument();
  });
  it('filters to show only Dish items when Dish filter is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<InventoryPage />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.queryByText('Tomato')).toBeInTheDocument();
    });

    const dishButton = screen.getByRole('button', { name: 'Dish' });
    await user.click(dishButton);

    // Tomato is Raw, Sauce is Prepped, Lasagna is Dish
    // We expect ONLY Lasagna
    expect(screen.queryByText('Tomato')).not.toBeInTheDocument();
    expect(screen.queryByText('Prepped Sauce')).not.toBeInTheDocument();
    expect(screen.getByText('Lasagna')).toBeInTheDocument();
  });
});
