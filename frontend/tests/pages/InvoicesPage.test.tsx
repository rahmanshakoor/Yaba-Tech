
import { render, screen, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import InvoicesPage from '../../src/pages/InvoicesPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import api from '../../src/services/api';

// Mock the API
vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const renderWithProviders = (ui: React.ReactNode) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('InvoicesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    queryClient.clear();
  });

  const mockInvoices = [
    {
      invoice_id: 1,
      supplier_name: 'Test Supplier',
      total_cost: 100.0,
      invoice_date: '2023-10-27T10:00:00',
      created_at: '2023-10-27T10:00:00',
      batches: [
        {
          batch_id: 101,
          item_id: 1,
          item_name: 'Flour',
          quantity_initial: 10,
          quantity_current: 10,
          unit: 'kg',
          unit_cost: 10.0,
          expiration_date: '2023-11-27T10:00:00',
        }
      ]
    },
  ];

  it('renders invoice list and details with batches', async () => {
    (api.get as any).mockResolvedValue({ data: mockInvoices });

    renderWithProviders(<InvoicesPage />);

    // Check if invoice is in the list
    expect(await screen.findByText('Test Supplier')).toBeInTheDocument();

    // Click on the invoice
    fireEvent.click(screen.getByText('Test Supplier'));

    // Check for details
    expect(await screen.findByText('Invoice #1')).toBeInTheDocument();

    // Check for batch details
    expect(screen.getByText('Items Received')).toBeInTheDocument();

    // Find the row containing 'Flour'
    const flourRow = screen.getByRole('row', { name: /Flour/i });
    expect(flourRow).toBeInTheDocument();

    const { getByText } = within(flourRow);
    expect(getByText('Flour')).toBeInTheDocument();
    expect(getByText('10 kg')).toBeInTheDocument();
    expect(getByText('$10.00')).toBeInTheDocument();
    expect(getByText('$100.00')).toBeInTheDocument();
  });

  it('shows empty state when no invoice selected', async () => {
    (api.get as any).mockResolvedValue({ data: mockInvoices });
    renderWithProviders(<InvoicesPage />);

    expect(await screen.findByText('Select an invoice to view details')).toBeInTheDocument();
  });
});
