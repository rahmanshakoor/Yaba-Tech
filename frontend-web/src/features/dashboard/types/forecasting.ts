export interface ForecastItem {
  item_id: number;
  name: string;
  type: 'Dish' | 'Prepped';
  predicted_demand: number;
  current_stock: number;
  recommended_action: number;
  unit: string;
}
