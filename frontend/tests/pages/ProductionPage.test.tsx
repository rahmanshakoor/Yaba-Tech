import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test-utils';
import ProductionPage from '../../src/pages/ProductionPage';

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn().mockImplementation((url: string) => {
      if (url === '/items/') {
        return Promise.resolve({ data: [
          { item_id: 1, name: 'Margherita Pizza', unit: 'pieces', type: 'Dish', shelf_life_days: 1, is_archived: false },
          { item_id: 2, name: 'Tomato Sauce', unit: 'liters', type: 'Prepped', shelf_life_days: 3, is_archived: false },
          { item_id: 3, name: 'Tomato', unit: 'kg', type: 'Raw', shelf_life_days: 7, is_archived: false },
        ]});
      }
      if (url === '/inventory/summary') {
        return Promise.resolve({ data: {
          items: [
            { item_id: 1, item_name: 'Margherita Pizza', unit: 'pieces', total_stock: 10, unit_cost: 5, total_value: 50 },
            { item_id: 2, item_name: 'Tomato Sauce', unit: 'liters', total_stock: 20, unit_cost: 2, total_value: 40 },
            { item_id: 3, item_name: 'Tomato', unit: 'kg', total_stock: 15, unit_cost: 1, total_value: 15 },
          ],
          total_inventory_value: 105,
        }});
      }
      return Promise.resolve({ data: { ingredients: [] } });
    }),
    post: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

describe('ProductionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the Chef Mode form', async () => {
    renderWithProviders(<ProductionPage />);
    await waitFor(() => {
      expect(screen.getByText('Chef Mode')).toBeInTheDocument();
    });
    expect(screen.getByText('Produce')).toBeInTheDocument();
  });

  it('shows a validation error when trying to produce without selecting an item', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProductionPage />);

    await waitFor(() => {
      expect(screen.getByText('Produce')).toBeInTheDocument();
    });

    const produceButton = screen.getByRole('button', { name: 'Produce' });
    await user.click(produceButton);

    expect(screen.getByText('Please select an item to produce.')).toBeInTheDocument();
  });

  it('only shows Dish and Prepped items in the dropdown', async () => {
    renderWithProviders(<ProductionPage />);

    await waitFor(() => {
      expect(screen.getByText('Margherita Pizza (Dish)')).toBeInTheDocument();
    });
    expect(screen.getByText('Tomato Sauce (Prepped)')).toBeInTheDocument();

    // Raw items should not appear in the produce dropdown options
    const select = screen.getByLabelText('Select Item');
    const options = Array.from(select.querySelectorAll('option'));
    const optionTexts = options.map((o) => o.textContent);
    expect(optionTexts).not.toContain('Tomato (Raw)');
  });

  it('clicking the Deplete tab hides the Produce form and shows the Deplete form', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProductionPage />);

    // Initially the Produce form is shown
    await waitFor(() => {
      expect(screen.getByText('Chef Mode')).toBeInTheDocument();
    });
    expect(screen.queryByText('Deplete Stock')).not.toBeInTheDocument();

    // Click the deplete tab
    await user.click(screen.getByRole('button', { name: 'Record Depletion' }));

    // Produce form should be gone, Deplete form should be visible
    expect(screen.queryByText('Chef Mode')).not.toBeInTheDocument();
    expect(screen.getByText('Deplete Stock')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Log Depletion' })).toBeInTheDocument();
  });

  it('disables submit and shows error when depleting more than available stock', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProductionPage />);

    // Switch to deplete mode
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Record Depletion' })).toBeInTheDocument();
    });
    await user.click(screen.getByRole('button', { name: 'Record Depletion' }));

    await waitFor(() => {
      expect(screen.getByText('Deplete Stock')).toBeInTheDocument();
    });

    // Select an item that has 10 in stock
    const select = screen.getByLabelText('Select Item');
    await user.selectOptions(select, '1');

    // Enter quantity of 50 (more than 10 available)
    const qtyInput = screen.getByLabelText('Quantity');
    await user.type(qtyInput, '50');

    // Should show insufficient stock error and disable the button
    expect(screen.getByText('Insufficient stock available.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Log Depletion' })).toBeDisabled();
  });
});
