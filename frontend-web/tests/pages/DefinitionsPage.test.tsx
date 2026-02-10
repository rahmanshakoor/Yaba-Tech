import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test-utils';
import DefinitionsPage from '../../src/pages/DefinitionsPage';

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [
      { item_id: 1, name: 'Tomato', unit: 'kg', type: 'Raw', shelf_life_days: 7, is_archived: false },
      { item_id: 2, name: 'Pasta', unit: 'kg', type: 'Raw', shelf_life_days: 30, is_archived: false },
    ]}),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

describe('DefinitionsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the Items tab by default with item data', async () => {
    renderWithProviders(<DefinitionsPage />);
    await waitFor(() => {
      expect(screen.getByText('Tomato')).toBeInTheDocument();
    });
    expect(screen.getByText('Pasta')).toBeInTheDocument();
  });

  it('opens the Add Item modal when clicking "Add Item Type"', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DefinitionsPage />);

    await waitFor(() => {
      expect(screen.getByText('Tomato')).toBeInTheDocument();
    });

    const addButton = screen.getByRole('button', { name: /add item type/i });
    await user.click(addButton);

    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Unit')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });
});
