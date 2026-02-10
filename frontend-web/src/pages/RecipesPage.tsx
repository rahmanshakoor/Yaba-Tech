import { useState } from 'react';
import { useItems } from '../hooks/useInventory';
import RecipeList from '../features/recipes/RecipeList';
import RecipeBuilder from '../features/recipes/RecipeBuilder';
import type { Item } from '../types';

export default function RecipesPage() {
  const { data: allItems = [] } = useItems();
  const dishes = allItems.filter((i) => i.type === 'Dish' || i.type === 'Prepped');
  const [selectedDish, setSelectedDish] = useState<Item | null>(null);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Recipes</h1>

      <div className="grid grid-cols-3 gap-6">
        {/* Left: Dish list */}
        <div className="col-span-1 bg-white border border-gray-200 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Dishes</h2>
          <RecipeList
            dishes={dishes}
            selectedId={selectedDish?.item_id ?? null}
            onSelect={setSelectedDish}
          />
        </div>

        {/* Right: Recipe builder */}
        <div className="col-span-2">
          {selectedDish ? (
            <RecipeBuilder dish={selectedDish} allItems={allItems} targetItemType={selectedDish.type} />
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
              Select a dish to view or edit its recipe
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
