import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import api from '../../services/api';
import { Input } from '../../components/common';
import { useDebounce } from '../../hooks/useDebounce';
import type { Item, Recipe } from '../../types';

interface RecipeBuilderProps {
  dish: Item;
  allItems: Item[];
}

export default function RecipeBuilder({ dish, allItems }: RecipeBuilderProps) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search);
  const [addQuantity, setAddQuantity] = useState<Record<number, string>>({});

  const { data: recipe } = useQuery<Recipe>({
    queryKey: ['recipe', dish.item_id],
    queryFn: async () => {
      const { data } = await api.get(`/items/${dish.item_id}/recipe`);
      return data;
    },
  });

  const addIngredient = useMutation({
    mutationFn: async ({
      inputItemId,
      quantity,
    }: {
      inputItemId: number;
      quantity: number;
    }) => {
      await api.post(`/items/${dish.item_id}/recipe`, {
        input_item_id: inputItemId,
        quantity_required: quantity,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipe', dish.item_id] });
    },
  });

  const availableItems = allItems.filter(
    (item) =>
      item.item_id !== dish.item_id &&
      item.name.toLowerCase().includes(debouncedSearch.toLowerCase()),
  );

  const handleAdd = (itemId: number) => {
    const qty = Number(addQuantity[itemId] || 1);
    if (qty <= 0) return;
    addIngredient.mutate({ inputItemId: itemId, quantity: qty });
    setAddQuantity((prev) => ({ ...prev, [itemId]: '' }));
  };

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
                onClick={() => handleAdd(item.item_id)}
                className="p-1 rounded hover:bg-indigo-50 text-indigo-600"
                title="Add to recipe"
              >
                <Plus size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Current recipe */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Recipe for {dish.name}
        </h3>
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
                <span className="font-mono text-gray-600">
                  {ing.quantity_required}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
