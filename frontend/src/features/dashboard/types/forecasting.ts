export interface ForecastItem {
  item_id: number;
  item_name: string;
  type: 'Dish' | 'Prepped' | 'Raw';
  predicted_demand: number;
  current_stock: number;
  gap: number;
  recommendation: string;
  unit: string;
}
