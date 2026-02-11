import type { Item } from '../../types';

interface RecipeListProps {
  dishes: Item[];
  selectedId: number | null;
  onSelect: (item: Item) => void;
}

export default function RecipeList({ dishes, selectedId, onSelect }: RecipeListProps) {
  return (
    <div className="space-y-1">
      {dishes.length === 0 ? (
        <p className="text-sm text-gray-400 py-4 text-center">No dishes found</p>
      ) : (
        dishes.map((dish) => (
          <button
            key={dish.item_id}
            onClick={() => onSelect(dish)}
            className={`w-full text-left px-4 py-3 rounded-md text-sm font-medium transition-colors ${selectedId === dish.item_id
                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                : 'hover:bg-gray-50 border border-transparent'
              }`}
          >
            <span className="block">{dish.name}</span>
            <span className="text-xs text-gray-400">{dish.type}</span>
          </button>
        ))
      )}
    </div>
  );
}
