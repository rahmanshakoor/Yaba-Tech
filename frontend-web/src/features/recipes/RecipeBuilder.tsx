import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2 } from 'lucide-react';
import api from '../../services/api';
import { Input } from '../../components/common';
import { useDebounce } from '../../hooks/useDebounce';
import { useInventorySummary } from '../../hooks/useInventory';
import type { Item, ItemType, Recipe } from '../../types';

interface SelectedIngredient {
  input_item_id: number;
  name: string;
  unit: string;
  quantity: number;
}

interface RecipeBuilderProps {
  dish: Item;
  allItems: Item[];
  targetItemType: ItemType;
}

export default function RecipeBuilder({ dish, allItems, targetItemType }: RecipeBuilderProps) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search);
  const [ingredients, setIngredients] = useState<SelectedIngredient[]>([]);
  const [addQuantity, setAddQuantity] = useState<Record<number, string>>({});
  const { data: summaryData } = useInventorySummary();

  const costMap = useMemo(() => {
    const map = new Map<number, number>();
    if (summaryData?.items) {
      summaryData.items.forEach((s) => map.set(s.item_id, s.unit_cost));
    }
    return map;
  }, [summaryData]);

  const { data: recipe } = useQuery<Recipe>({
    queryKey: ['recipe', dish.item_id],
    queryFn: async () => {
      const { data } = await api.get(`/items/${dish.item_id}/recipe`);
      return data;
    },
  });

  const saveComposition = useMutation({
    mutationFn: async (payload: { input_item_id: number; quantity: number }[]) => {
      await api.post(`/items/${dish.item_id}/composition`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipe', dish.item_id] });
      setIngredients([]);
    },
  });

  // Filter available items based on targetItemType
  const availableItems = allItems.filter((item) => {
    if (item.item_id === dish.item_id) return false;
    if (!item.name.toLowerCase().includes(debouncedSearch.toLowerCase())) return false;

    if (targetItemType === 'Prepped') {
      return item.type === 'Raw';
    }
    if (targetItemType === 'Dish') {
      return item.type === 'Raw' || item.type === 'Prepped';
    }
    return false;
  });

  const handleAdd = (item: Item) => {
    const qty = Number(addQuantity[item.item_id] || 1);
    if (qty <= 0) return;

    // Avoid duplicates
    if (ingredients.some((ing) => ing.input_item_id === item.item_id)) return;

    setIngredients((prev) => [
      ...prev,
      { input_item_id: item.item_id, name: item.name, unit: item.unit, quantity: qty },
    ]);
    setAddQuantity((prev) => ({ ...prev, [item.item_id]: '' }));
  };

  const handleRemove = (inputItemId: number) => {
    setIngredients((prev) => prev.filter((ing) => ing.input_item_id !== inputItemId));
  };

  const handleSave = () => {
    if (ingredients.length === 0) return;
    saveComposition.mutate(
      ingredients.map((ing) => ({
        input_item_id: ing.input_item_id,
        quantity: ing.quantity,
      })),
    );
  };

  // Estimated cost for pending ingredients
  const pendingEstimatedCost = useMemo(() => {
    return ingredients.reduce((sum, ing) => {
      const ingCost = costMap.get(ing.input_item_id) ?? 0;
      return sum + ing.quantity * ingCost;
    }, 0);
  }, [ingredients, costMap]);

  // Estimated cost for saved recipe
  const savedRecipeCost = useMemo(() => {
    if (!recipe?.ingredients?.length) return 0;
    return recipe.ingredients.reduce((sum, ing) => {
      const ingCost = costMap.get(ing.input_item_id) ?? 0;
      return sum + ing.quantity_required * ingCost;
    }, 0);
  }, [recipe, costMap]);

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Left: Available ingredients */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Available Ingredients
        </h3>
        <Input
          placeholder="Search ingredients..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mb-3"
        />
        <div className="border border-gray-200 rounded-lg max-h-80 overflow-y-auto divide-y divide-gray-100">
          {availableItems.map((item) => (
            <div
              key={item.item_id}
              className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50"
            >
              <span className="flex-1">
                {item.name}{' '}
                <span className="text-gray-400">({item.unit})</span>
              </span>
              <input
                type="number"
                className="w-16 border border-gray-300 rounded px-2 py-1 text-xs"
                placeholder="Qty"
                min="0.1"
                step="0.1"
                value={addQuantity[item.item_id] ?? ''}
                onChange={(e) =>
                  setAddQuantity((prev) => ({
                    ...prev,
                    [item.item_id]: e.target.value,
                  }))
                }
              />
              <button
                onClick={() => handleAdd(item)}
                className="p-1 rounded hover:bg-indigo-50 text-indigo-600"
                title="Add to recipe"
              >
                <Plus size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Current recipe + staged ingredients */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Recipe for {dish.name}
        </h3>

        {/* Staged ingredients (pending save) */}
        {ingredients.length > 0 && (
          <div className="mb-4">
            <h4 className="text-xs font-semibold text-gray-500 mb-2">
              Pending Ingredients
            </h4>
            <div className="border border-indigo-200 rounded-lg divide-y divide-indigo-100 bg-indigo-50">
              {ingredients.map((ing) => (
                <div
                  key={ing.input_item_id}
                  className="flex items-center justify-between px-4 py-3 text-sm"
                >
                  <span>
                    {ing.name}{' '}
                    <span className="text-gray-400">({ing.unit})</span>
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-gray-600">
                      {ing.quantity}
                    </span>
                    <button
                      onClick={() => handleRemove(ing.input_item_id)}
                      className="p-1 rounded hover:bg-red-50 text-red-500"
                      title="Remove ingredient"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={handleSave}
              disabled={saveComposition.isPending}
              className="mt-3 w-full px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {saveComposition.isPending ? 'Saving...' : 'Save Composition'}
            </button>
            {pendingEstimatedCost > 0 && (
              <div className="mt-2 text-sm text-indigo-700 font-medium text-right">
                Estimated Cost: ${pendingEstimatedCost.toFixed(2)}
              </div>
            )}
          </div>
        )}

        {/* Saved recipe */}
        <div className="border border-gray-200 rounded-lg divide-y divide-gray-100">
          {!recipe?.ingredients?.length ? (
            <p className="px-4 py-6 text-sm text-gray-400 text-center">
              No ingredients yet
            </p>
          ) : (
            recipe.ingredients.map((ing) => (
              <div
                key={ing.composition_id}
                className="flex items-center justify-between px-4 py-3 text-sm"
              >
                <span>{ing.input_item_name}</span>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-gray-600">
                    {ing.quantity_required}
                  </span>
                  <span className="font-mono text-gray-400 text-xs">
                    ${((costMap.get(ing.input_item_id) ?? 0) * ing.quantity_required).toFixed(2)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
        {savedRecipeCost > 0 && (
          <div className="mt-2 text-sm text-gray-700 font-medium text-right">
            Recipe Cost: ${savedRecipeCost.toFixed(2)}
          </div>
        )}
      </div>
    </div>
  );
}
