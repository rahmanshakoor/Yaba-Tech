from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models import ItemType


class ItemCreate(BaseModel):
    name: str
    unit: str
    shelf_life_days: int = 0
    type: ItemType


class ItemResponse(BaseModel):
    item_id: int
    name: str
    unit: str
    shelf_life_days: int
    type: ItemType

    model_config = {"from_attributes": True}


class ItemCompositionCreate(BaseModel):
    output_item_id: int
    input_item_id: int
    quantity_required: float


class ProductionRequest(BaseModel):
    output_item_id: int
    quantity_to_produce: float


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


class ReorderRecommendation(BaseModel):
    item_id: int
    item_name: str
    current_stock: float
    predicted_demand: float
    gap: float
    recommendation: str


class ForecastingResponse(BaseModel):
    recommendations: list[ReorderRecommendation]
