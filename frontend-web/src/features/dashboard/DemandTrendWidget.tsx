import { TrendingUp } from 'lucide-react';
import type { ForecastItem } from './types/forecasting';

interface DemandTrendWidgetProps {
  items: ForecastItem[];
}

export default function DemandTrendWidget({ items }: DemandTrendWidgetProps) {
  const topMovers = [...items]
    .sort((a, b) => b.predicted_demand - a.predicted_demand)
    .slice(0, 3);

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      <div className="px-5 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Top Movers</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          Highest predicted demand for tomorrow
        </p>
      </div>

      {topMovers.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-gray-400">
          No forecast data available.
        </p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {topMovers.map((item) => (
            <li
              key={item.item_id}
              className="px-5 py-3 flex items-center justify-between"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {item.name}
                </p>
                <p className="text-xs text-gray-500">{item.type}</p>
              </div>
              <div className="flex items-center gap-1.5 text-green-600">
                <TrendingUp size={14} />
                <span className="text-sm font-semibold">
                  {item.predicted_demand} {item.unit}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
