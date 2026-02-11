import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test-utils';
import DailyPrepList from '../../src/features/dashboard/DailyPrepList';
import DemandTrendWidget from '../../src/features/dashboard/DemandTrendWidget';
import type { ForecastItem } from '../../src/features/dashboard/types/forecasting';

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

const mockItems: ForecastItem[] = [
  {
    item_id: 1,
    item_name: 'Pizza Dough',
    type: 'Prepped',
    predicted_demand: 50,
    current_stock: 0,
    gap: 50,
    recommendation: 'Prep 50 kg',
    unit: 'kg',
  },
  {
    item_id: 2,
    item_name: 'Burger',
    type: 'Dish',
    predicted_demand: 80,
    current_stock: 40,
    gap: 40,
    recommendation: 'Prep 40 pcs',
    unit: 'pcs',
  },
  {
    item_id: 3,
    item_name: 'Caesar Salad',
    type: 'Dish',
    predicted_demand: 30,
    current_stock: 30,
    gap: 0,
    recommendation: 'None',
    unit: 'pcs',
  },
  {
    item_id: 4,
    item_name: 'Soup Base',
    type: 'Prepped',
    predicted_demand: 20,
    current_stock: 5,
    gap: 15,
    recommendation: 'Prep 15 liters',
    unit: 'liters',
  },
];

describe('DailyPrepList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows only items where gap > 0', () => {
    renderWithProviders(<DailyPrepList items={mockItems} />);
    expect(screen.getByText('Pizza Dough')).toBeInTheDocument();
    expect(screen.getByText('Burger')).toBeInTheDocument();
    expect(screen.getByText('Soup Base')).toBeInTheDocument();
    expect(screen.queryByText('Caesar Salad')).not.toBeInTheDocument();
  });

  it('sorts items by recommended_action descending', () => {
    renderWithProviders(<DailyPrepList items={mockItems} />);
    const rows = screen.getAllByRole('row');
    // row 0 is header, 1-3 are data rows
    expect(within(rows[1]).getByText('Pizza Dough')).toBeInTheDocument();
    expect(within(rows[2]).getByText('Burger')).toBeInTheDocument();
    expect(within(rows[3]).getByText('Soup Base')).toBeInTheDocument();
  });

  it('shows Critical badge for zero-stock items and Low for others', () => {
    renderWithProviders(<DailyPrepList items={mockItems} />);
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getAllByText('Low')).toHaveLength(2);
  });

  it('displays action text with quantity and unit', () => {
    renderWithProviders(<DailyPrepList items={mockItems} />);
    expect(screen.getByText('Prep 50 kg')).toBeInTheDocument();
    expect(screen.getByText('Prep 40 pcs')).toBeInTheDocument();
    expect(screen.getByText('Prep 15 liters')).toBeInTheDocument();
  });

  it('grays out row when Done button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DailyPrepList items={mockItems} />);

    const doneButton = screen.getByLabelText('Mark Pizza Dough done');
    await user.click(doneButton);

    const row = screen.getByText('Pizza Dough').closest('tr');
    expect(row).toHaveClass('opacity-40');
  });

  it('shows empty message when no items need prep', () => {
    renderWithProviders(<DailyPrepList items={[]} />);
    expect(
      screen.getByText('All caught up — nothing to prep.'),
    ).toBeInTheDocument();
  });
});

describe('DemandTrendWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows top 3 items by predicted demand', () => {
    renderWithProviders(<DemandTrendWidget items={mockItems} />);
    expect(screen.getByText('Burger')).toBeInTheDocument();
    expect(screen.getByText('Pizza Dough')).toBeInTheDocument();
    expect(screen.getByText('Caesar Salad')).toBeInTheDocument();
    expect(screen.queryByText('Soup Base')).not.toBeInTheDocument();
  });

  it('displays predicted demand with unit', () => {
    renderWithProviders(<DemandTrendWidget items={mockItems} />);
    expect(screen.getByText('80 pcs')).toBeInTheDocument();
    expect(screen.getByText('50 kg')).toBeInTheDocument();
    expect(screen.getByText('30 pcs')).toBeInTheDocument();
  });

  it('shows empty message when no items provided', () => {
    renderWithProviders(<DemandTrendWidget items={[]} />);
    expect(
      screen.getByText('No forecast data available.'),
    ).toBeInTheDocument();
  });
});
