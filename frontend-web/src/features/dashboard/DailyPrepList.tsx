import { useState } from 'react';
import { Check } from 'lucide-react';
import type { ForecastItem } from './types/forecasting';

interface DailyPrepListProps {
  items: ForecastItem[];
}

export default function DailyPrepList({ items }: DailyPrepListProps) {
  const [doneIds, setDoneIds] = useState<Set<number>>(new Set());

  const prepItems = items
    .filter((item) => item.recommended_action > 0)
    .sort((a, b) => b.recommended_action - a.recommended_action);

  const markDone = (id: number) => {
    setDoneIds((prev) => new Set(prev).add(id));
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      <div className="px-5 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Daily Prep List
        </h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Items to prepare for tomorrow
        </p>
      </div>

      {prepItems.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-gray-400">
          All caught up — nothing to prep.
        </p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-500">
              <th className="px-5 py-3">Item</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Action</th>
              <th className="px-5 py-3 w-16"></th>
            </tr>
          </thead>
          <tbody>
            {prepItems.map((item) => {
              const isDone = doneIds.has(item.item_id);
              const isCritical = item.current_stock === 0;
              return (
                <tr
                  key={item.item_id}
                  className={`border-b border-gray-50 ${isDone ? 'opacity-40' : ''}`}
                >
                  <td className="px-5 py-3 font-medium text-gray-900">
                    {item.name}
                  </td>
                  <td className="px-5 py-3">
                    {isCritical ? (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Critical
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                        Low
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 font-bold text-gray-900">
                    Prep {item.recommended_action} {item.unit}
                  </td>
                  <td className="px-5 py-3">
                    <button
                      type="button"
                      disabled={isDone}
                      onClick={() => markDone(item.item_id)}
                      aria-label={`Mark ${item.name} done`}
                      className="p-1.5 rounded-md hover:bg-green-50 text-gray-400 hover:text-green-600 disabled:cursor-default disabled:hover:bg-transparent"
                    >
                      <Check size={16} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
