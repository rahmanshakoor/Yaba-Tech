import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test-utils';
import InvoicesPage from '../../src/pages/InvoicesPage';

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

describe('InvoicesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('opens the Add Invoice modal when clicking "Add Invoice"', async () => {
    const user = userEvent.setup();
    renderWithProviders(<InvoicesPage />);

    const addButton = screen.getByRole('button', { name: /add invoice/i });
    await user.click(addButton);

    expect(screen.getByText('Auto OCR')).toBeInTheDocument();
    expect(screen.getByText('Manually')).toBeInTheDocument();
  });

  it('shows the Manual form with Add Row when selecting "Manually"', async () => {
    const user = userEvent.setup();
    renderWithProviders(<InvoicesPage />);

    const addButton = screen.getByRole('button', { name: /add invoice/i });
    await user.click(addButton);

    const manualButton = screen.getByText('Manually');
    await user.click(manualButton);

    await waitFor(() => {
      expect(screen.getByText('Add Row')).toBeInTheDocument();
    });
  });

  it('allows adding multiple rows of ingredients in Manual form', async () => {
    const user = userEvent.setup();
    renderWithProviders(<InvoicesPage />);

    const addButton = screen.getByRole('button', { name: /add invoice/i });
    await user.click(addButton);

    const manualButton = screen.getByText('Manually');
    await user.click(manualButton);

    await waitFor(() => {
      expect(screen.getByText('Add Row')).toBeInTheDocument();
    });

    // Initially should have 1 row
    const initialRows = screen.getAllByPlaceholderText('Qty');
    expect(initialRows).toHaveLength(1);

    // Click Add Row
    const addRowButton = screen.getByText('Add Row');
    await user.click(addRowButton);

    // Should have 2 rows now
    const updatedRows = screen.getAllByPlaceholderText('Qty');
    expect(updatedRows).toHaveLength(2);

    // Add another row
    await user.click(addRowButton);
    const finalRows = screen.getAllByPlaceholderText('Qty');
    expect(finalRows).toHaveLength(3);
  });
});
