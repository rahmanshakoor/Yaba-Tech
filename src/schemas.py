from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models import ItemType, WasteReason


class ItemCreate(BaseModel):
    name: str
    unit: str
    shelf_life_days: int = 0
    type: ItemType


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    shelf_life_days: Optional[int] = None


class ItemResponse(BaseModel):
    item_id: int
    name: str
    unit: str
    shelf_life_days: int
    type: ItemType
    is_archived: bool = False

    model_config = {"from_attributes": True}


class RecipeIngredient(BaseModel):
    input_item_id: int
    quantity_required: float


class RecipeIngredientResponse(BaseModel):
    composition_id: int
    input_item_id: int
    input_item_name: str
    quantity_required: float

    model_config = {"from_attributes": True}


class RecipeResponse(BaseModel):
    output_item_id: int
    output_item_name: str
    ingredients: list[RecipeIngredientResponse]


class ItemCompositionCreate(BaseModel):
    output_item_id: int
    input_item_id: int
    quantity_required: float


class CompositionIngredient(BaseModel):
    input_item_id: int
    quantity: float


class CompositionResponse(BaseModel):
    output_item_id: int
    compositions: list[RecipeIngredientResponse]


class ManualInvoiceLineItem(BaseModel):
    item_id: int
    quantity: float
    unit_cost: float
    is_short_shipment: Optional[bool] = False


class ManualInvoiceCreate(BaseModel):
    supplier_name: str
    date: Optional[str] = None
    total_cost: float
    items: list[ManualInvoiceLineItem]


class InvoiceResponse(BaseModel):
    invoice_id: int
    supplier_name: str
    total_cost: float
    invoice_date: Optional[datetime] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProductionRequest(BaseModel):
    output_item_id: int
    quantity_to_produce: float
    manual_batches: Optional[dict[int, int]] = None  # input_item_id -> batch_id



class ProductionResponse(BaseModel):
    output_batch_id: int
    output_item_id: int
    quantity_produced: float
    ingredients_used: list[dict]


class InvoiceUploadResponse(BaseModel):
    invoice_id: int
    supplier_name: str
    total_cost: float
    image_url: Optional[str] = None
    items_added: list[dict]


class InventoryBatchResponse(BaseModel):
    batch_id: int
    item_id: int
    quantity_current: float
    quantity_initial: float
    expiration_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InventorySummaryItem(BaseModel):
    item_id: int
    item_name: str
    unit: str
    total_stock: float
    unit_cost: float = 0.0
    total_value: float = 0.0


class InventorySummaryResponse(BaseModel):
    items: list[InventorySummaryItem]
    total_inventory_value: float = 0.0


class BatchUpdateRequest(BaseModel):
    quantity_current: float


class ManualProductionRequest(BaseModel):
    output_item_id: int
    quantity_to_produce: float
    input_batches: Optional[list[dict]] = None


class ReorderRecommendation(BaseModel):
    item_id: int
    item_name: str
    unit: str
    type: ItemType
    current_stock: float
    predicted_demand: float
    gap: float
    recommendation: str


class ForecastingResponse(BaseModel):
    recommendations: list[ReorderRecommendation]


class WasteRequest(BaseModel):
    batch_id: int
    quantity: float
    reason: WasteReason


class WasteResponse(BaseModel):
    waste_id: int
    batch_id: int
    quantity: float
    reason: WasteReason
    cost_loss: float

    model_config = {"from_attributes": True}
