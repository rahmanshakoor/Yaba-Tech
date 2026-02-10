from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models import (
    Item,
    ItemsInventory,
    ProductionLog,
    Invoice,
    WasteLog,
    ItemType,
)
from src.schemas import (
    ProductionResponse,
)
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    lowStockItems: int
    todaysProductionCost: float
    pendingInvoices: int
    wasteValueWeek: float


class DashboardLog(BaseModel):
    log_id: int
    output_batch_id: int
    input_batch_id: int
    quantity_used: float
    created_at: datetime
    output_item_name: str
    input_item_name: str

    class Config:
        from_attributes = True


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated statistics for the dashboard.
    """
    # 1. Low Stock Items (Total stock < 5)
    # This is a bit complex because stock is across batches.
    # We first sum up stock per item, then count how many items have sum < 5.
    # For simplicity and performance in this MVP, we might just query all items and their batches.
    # A more optimized SQL query would be better for large datasets.
    
    # Logic:
    #   SELECT count(*) FROM (
    #       SELECT item_id, SUM(quantity_current) as total
    #       FROM items_inventory
    #       GROUP BY item_id
    #       HAVING total < 5
    #   )
    
    # However, SqlAlchemy async with HAVING can be tricky.
    # Let's do a Python-side aggregation for now as we likely have few items.
    
    # Get all active items
    all_items_result = await db.execute(select(Item).where(Item.is_archived == False))
    all_items = all_items_result.scalars().all()
    
    low_stock_count = 0
    for item in all_items:
        batches_result = await db.execute(
            select(func.sum(ItemsInventory.quantity_current))
            .where(ItemsInventory.item_id == item.item_id)
        )
        total_stock = batches_result.scalar() or 0
        if total_stock < 5:
            low_stock_count += 1

    # 2. Today's Production Cost
    # Sum of quantity_used * input_batch.unit_cost for logs created today.
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # We need to join ProductionLog with ItemsInventory to access unit_cost
    production_cost_result = await db.execute(
        select(func.sum(ProductionLog.quantity_used * ItemsInventory.unit_cost))
        .join(ItemsInventory, ProductionLog.input_batch_id == ItemsInventory.batch_id)
        .where(ProductionLog.created_at >= today_start)
    )
    todays_production_cost = production_cost_result.scalar() or 0.0

    # 3. Pending Invoices
    # For now, let's just count all invoices. We don't have a "status" field on Invoice yet.
    # If "pending" means "not yet processed into inventory", that's tricky because 
    # currently ingestion creates invoice AND inventory batches transactions.
    # So effectively all invoices in the system are "processed".
    # But the frontend was showing a number. Let's just return total invoices for now,
    # or maybe invoices from the last 30 days to keep it "recent".
    # Or strict interpretation: 0 pending if everything is processed immediately.
    # The original frontend code `(invoicesRes.data || []).length` suggests it was just counting all fetched invoices.
    # let's count all invoices for now.
    invoices_count_result = await db.execute(select(func.count(Invoice.invoice_id)))
    pending_invoices = invoices_count_result.scalar() or 0

    # 4. Waste Value (Week)
    # Sum of cost_loss for logs created in the last 7 days.
    week_start = datetime.now() - timedelta(days=7)
    waste_value_result = await db.execute(
        select(func.sum(WasteLog.cost_loss))
        .where(WasteLog.created_at >= week_start)
    )
    waste_value_week = waste_value_result.scalar() or 0.0

    return DashboardStats(
        lowStockItems=low_stock_count,
        todaysProductionCost=todays_production_cost,
        pendingInvoices=pending_invoices,
        wasteValueWeek=waste_value_week,
    )


@router.get("/recent-logs")
async def get_recent_logs(db: AsyncSession = Depends(get_db)):
    """
    Get 5 most recent production logs with item names.
    """
    # We need to join with ItemsInventory -> Item to get names.
    # ProductionLog -> input_batch (ItemsInventory) -> Item
    # ProductionLog -> output_batch (ItemsInventory) -> Item
    
    # We can use eager loading.
    
    result = await db.execute(
        select(ProductionLog)
        .options(
            selectinload(ProductionLog.input_batch).selectinload(ItemsInventory.item),
            selectinload(ProductionLog.output_batch).selectinload(ItemsInventory.item),
        )
        .order_by(desc(ProductionLog.created_at))
        .limit(5)
    )
    logs = result.scalars().all()
    
    dashboard_logs = []
    for log in logs:
        # Safety checks in case batches/items are missing/deleted (though FK should prevent this)
        input_name = "Unknown"
        output_name = "Unknown"
        
        if log.input_batch and log.input_batch.item:
            input_name = log.input_batch.item.name
            
        if log.output_batch and log.output_batch.item:
            output_name = log.output_batch.item.name

        dashboard_logs.append({
            "log_id": log.log_id,
            "output_batch_id": log.output_batch_id,
            "input_batch_id": log.input_batch_id,
            "quantity_used": log.quantity_used,
            "created_at": log.created_at,
            "output_item_name": output_name,
            "input_item_name": input_name,
        })
        
    return dashboard_logs
