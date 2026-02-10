export type ItemType = 'Raw' | 'Prepped' | 'Dish';
export type WasteReason = 'Spoiled' | 'Dropped' | 'Burned' | 'Theft';

export interface Item {
  item_id: number;
  name: string;
  unit: string;
  shelf_life_days: number;
  type: ItemType;
  is_archived: boolean;
}

export interface InventoryBatch {
  batch_id: number;
  item_id: number;
  quantity_current: number;
  quantity_initial: number;
  expiration_date: string | null;
}

export interface InventorySummaryItem {
  item_id: number;
  item_name: string;
  unit: string;
  total_stock: number;
}

export interface RecipeIngredient {
  composition_id: number;
  input_item_id: number;
  input_item_name: string;
  quantity_required: number;
}

export interface Recipe {
  output_item_id: number;
  output_item_name: string;
  ingredients: RecipeIngredient[];
}

export interface ProductionLog {
  log_id: number;
  output_batch_id: number;
  input_batch_id: number;
  quantity_used: number;
  created_at: string;
}

export interface Invoice {
  invoice_id: number;
  supplier_name: string;
  total_cost: number;
  invoice_date: string | null;
  image_url: string | null;
  created_at: string | null;
}

export interface WasteLog {
  waste_id: number;
  batch_id: number;
  quantity: number;
  reason: WasteReason;
  cost_loss: number;
}

export interface DashboardKPIs {
  lowStockItems: number;
  todaysProductionCost: number;
  pendingInvoices: number;
  wasteValueWeek: number;
}

export interface ProductionResponse {
  output_batch_id: number;
  output_item_id: number;
  quantity_produced: number;
  ingredients_used: Record<string, unknown>[];
}
