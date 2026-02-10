import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test-utils';
import RecipeBuilder from '../../src/features/recipes/RecipeBuilder';
import type { Item } from '../../src/types';

vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { ingredients: [] } }),
    post: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

const rawTomato: Item = { item_id: 1, name: 'Tomato', unit: 'kg', type: 'Raw', shelf_life_days: 7, is_archived: false };
const rawOnion: Item = { item_id: 2, name: 'Onion', unit: 'kg', type: 'Raw', shelf_life_days: 14, is_archived: false };
const preppedSalsa: Item = { item_id: 3, name: 'Salsa', unit: 'liters', type: 'Prepped', shelf_life_days: 3, is_archived: false };
const dishPizza: Item = { item_id: 4, name: 'Pizza', unit: 'pieces', type: 'Dish', shelf_life_days: 1, is_archived: false };

const allItems: Item[] = [rawTomato, rawOnion, preppedSalsa, dishPizza];

describe('RecipeBuilder', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows only Raw items when targetItemType is Prepped', async () => {
    renderWithProviders(
      <RecipeBuilder dish={preppedSalsa} allItems={allItems} targetItemType="Prepped" />
    );

    await waitFor(() => {
      expect(screen.getByText(/Tomato/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Onion/)).toBeInTheDocument();

    // Prepped and Dish items should NOT be shown
    expect(screen.queryByText(/Pizza/)).not.toBeInTheDocument();
    // The dish (Salsa) itself is excluded as the target
  });

  it('shows Raw and Prepped items when targetItemType is Dish', async () => {
    renderWithProviders(
      <RecipeBuilder dish={dishPizza} allItems={allItems} targetItemType="Dish" />
    );

    await waitFor(() => {
      expect(screen.getByText(/Tomato/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Onion/)).toBeInTheDocument();
    expect(screen.getByText(/Salsa/)).toBeInTheDocument();

    // Other Dish items should NOT be shown
    // (Pizza is the target dish itself, already excluded)
  });

  it('adds an ingredient to the pending list and shows Save button', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <RecipeBuilder dish={preppedSalsa} allItems={allItems} targetItemType="Prepped" />
    );

    await waitFor(() => {
      expect(screen.getByText(/Tomato/)).toBeInTheDocument();
    });

    // Click add button for Tomato
    const addButtons = screen.getAllByTitle('Add to recipe');
    await user.click(addButtons[0]);

    // Pending section should appear with Save button
    expect(screen.getByText('Save Composition')).toBeInTheDocument();
    expect(screen.getByText('Pending Ingredients')).toBeInTheDocument();
  });

  it('removes an ingredient from the pending list', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <RecipeBuilder dish={preppedSalsa} allItems={allItems} targetItemType="Prepped" />
    );

    await waitFor(() => {
      expect(screen.getByText(/Tomato/)).toBeInTheDocument();
    });

    // Add ingredient
    const addButtons = screen.getAllByTitle('Add to recipe');
    await user.click(addButtons[0]);

    expect(screen.getByText('Save Composition')).toBeInTheDocument();

    // Remove ingredient
    const removeButton = screen.getByTitle('Remove ingredient');
    await user.click(removeButton);

    // Save button should disappear when no pending ingredients
    expect(screen.queryByText('Save Composition')).not.toBeInTheDocument();
  });
});
