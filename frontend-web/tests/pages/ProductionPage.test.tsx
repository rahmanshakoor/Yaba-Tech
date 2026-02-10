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

    // Raw items should not appear in the dropdown options
    const options = screen.getAllByRole('option');
    const optionTexts = options.map((o) => o.textContent);
    expect(optionTexts).not.toContain('Tomato (Raw)');
  });
});
