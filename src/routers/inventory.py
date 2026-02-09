"""Inventory management router for stock corrections and manual production."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Item, ItemsInventory, WasteLog
from src.schemas import (
    BatchUpdateRequest,
    InventoryBatchResponse,
    InventorySummaryItem,
    InventorySummaryResponse,
    ManualProductionRequest,
    ProductionResponse,
    WasteRequest,
    WasteResponse,
)
from src.services.inventory_service import produce_item

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/summary", response_model=InventorySummaryResponse)
async def inventory_summary(
    db: AsyncSession = Depends(get_db),
):
    """Returns current total stock grouped by Item."""
    items_result = await db.execute(select(Item).where(Item.is_archived.is_(False)))
    items = items_result.scalars().all()

    summary_items = []
    for item in items:
        batches_result = await db.execute(
            select(ItemsInventory).where(
                ItemsInventory.item_id == item.item_id,
                ItemsInventory.quantity_current > 0,
            )
        )
        batches = batches_result.scalars().all()
        total = sum(b.quantity_current for b in batches)
        if total > 0:
            summary_items.append(
                InventorySummaryItem(
                    item_id=item.item_id,
                    item_name=item.name,
                    unit=item.unit,
                    total_stock=total,
                )
            )

    return InventorySummaryResponse(items=summary_items)


@router.get("/batches/{item_id}", response_model=list[InventoryBatchResponse])
async def get_item_batches(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Returns specific physical batches for an item."""
    result = await db.execute(
        select(ItemsInventory)
        .where(
            ItemsInventory.item_id == item_id,
            ItemsInventory.quantity_current > 0,
        )
        .order_by(ItemsInventory.created_at.asc())
    )
    return result.scalars().all()


@router.put("/batch/{batch_id}", response_model=InventoryBatchResponse)
async def update_batch(
    batch_id: int,
    update: BatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Manually override batch quantity (e.g., stock-taking corrections)."""
    result = await db.execute(
        select(ItemsInventory).where(ItemsInventory.batch_id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch.quantity_current = update.quantity_current
    await db.commit()
    await db.refresh(batch)
    return batch


@router.post("/production/manual", response_model=ProductionResponse)
async def manual_production(
    request: ManualProductionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Trigger production manually via API (deducts raw, adds prepped)."""
    try:
        result = await produce_item(
            db,
            output_item_id=request.output_item_id,
            quantity_to_produce=request.quantity_to_produce,
        )
        return ProductionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/waste", response_model=WasteResponse, status_code=201)
async def log_waste(
    request: WasteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Log waste: deduct quantity from a batch and record the financial loss."""
    result = await db.execute(
        select(ItemsInventory).where(ItemsInventory.batch_id == request.batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if request.quantity > batch.quantity_current:
        raise HTTPException(
            status_code=400,
            detail="Waste quantity exceeds current batch quantity",
        )

    # Calculate cost loss proportionally from the batch
    # Note: Without per-unit cost data on batches, we use a unit cost of 1.0
    # as a placeholder. In a production system, this would be derived from the
    # source invoice's line item cost.
    if batch.quantity_initial > 0:
        cost_loss = request.quantity * 1.0
    else:
        cost_loss = 0.0

    batch.quantity_current -= request.quantity

    waste_entry = WasteLog(
        batch_id=request.batch_id,
        quantity=request.quantity,
        reason=request.reason,
        cost_loss=cost_loss,
    )
    db.add(waste_entry)
    await db.commit()
    await db.refresh(waste_entry)
    return waste_entry
