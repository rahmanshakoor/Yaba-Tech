import { useQuery } from '@tanstack/react-query';
import api from '../../../services/api';
import type { ForecastItem } from '../types/forecasting';

function generateMockData(): ForecastItem[] {
  const items: { name: string; type: 'Dish' | 'Prepped'; unit: string }[] = [
    { name: 'Burger', type: 'Dish', unit: 'pcs' },
    { name: 'Pizza Dough', type: 'Prepped', unit: 'kg' },
    { name: 'Caesar Salad', type: 'Dish', unit: 'pcs' },
    { name: 'Grilled Chicken', type: 'Dish', unit: 'pcs' },
    { name: 'Soup Base', type: 'Prepped', unit: 'liters' },
    { name: 'Pasta Sauce', type: 'Prepped', unit: 'liters' },
    { name: 'Fries', type: 'Prepped', unit: 'kg' },
    { name: 'Fish Tacos', type: 'Dish', unit: 'pcs' },
  ];

  return items.map((item, index) => {
    const predicted = Math.floor(Math.random() * 60) + 10;
    const stock = Math.floor(Math.random() * predicted);
    const gap = predicted - stock;
    return {
      item_id: index + 1,
      item_name: item.name,
      type: item.type,
      predicted_demand: predicted,
      current_stock: stock,
      gap: gap,
      recommendation: `Order ${gap} ${item.unit} of ${item.name}`,
      unit: item.unit,
    };
  });
}

export function useDashboardForecast() {
  return useQuery<ForecastItem[]>({
    queryKey: ['dashboardForecast'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/forecasting/reorder-recommendations', {
          params: {
            forecast_days: 1,
            threshold: 0,
          },
        });
        // The backend returns { recommendations: [...] }, so we need to extract the array
        return data.recommendations;
      } catch {
        return generateMockData();
      }
    },
  });
}
