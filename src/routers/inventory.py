"""Inventory management router for stock corrections and manual production."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Item, ItemComposition, ItemsInventory, WasteLog
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



@router.get("/batches", response_model=list[InventoryBatchResponse])
async def get_all_batches(
    db: AsyncSession = Depends(get_db),
):
    """Returns all active physical batches."""
    result = await db.execute(
        select(ItemsInventory)
        .where(ItemsInventory.quantity_current > 0)
        .order_by(ItemsInventory.created_at.desc())
    )
    return result.scalars().all()


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
    await db.refresh(batch)
    return batch


@router.get("/check-stock/{item_id}")
async def check_stock(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Check if all ingredients for an item exist in inventory."""
    # 1. Get ingredients
    from sqlalchemy.orm import joinedload
    result = await db.execute(
        select(ItemComposition)
        .options(joinedload(ItemComposition.input_item))
        .where(ItemComposition.output_item_id == item_id)
    )
    ingredients = result.scalars().all()

    if not ingredients:
        # No recipe means we can't produce it (or it's a raw item), so stock check for "ingredients" fails or is applicable
        # The prompt implies looking for ingredients. If no ingredients, we can't verify "all ingredients exist".
        # Returning False matches the behavior of "cannot produce".
        return {"available": False, "detail": "No recipe defined"}

    # 2. Check stock for each ingredient
    max_producible = float('inf')
    missing_details = []

    for ing in ingredients:
        # Get total stock for this ingredient
        stock_result = await db.execute(
            select(ItemsInventory)
            .where(
                ItemsInventory.item_id == ing.input_item_id,
                ItemsInventory.quantity_current > 0,
            )
        )
        batches = stock_result.scalars().all()
        total_stock = sum(b.quantity_current for b in batches)
        
        # Calculate max possible for this ingredient
        if ing.quantity_required > 0:
            possible = int(total_stock / ing.quantity_required)
            if possible < max_producible:
                max_producible = possible

        if total_stock < ing.quantity_required:
             missing_details.append(f"{ing.input_item.name} (have {total_stock}, need {ing.quantity_required})")

    if max_producible == float('inf'):
        max_producible = 0

    if missing_details:
        return {
            "available": False, 
            "detail": f"Missing: {', '.join(missing_details)}",
            "max_producible": max_producible
        }
            
    return {"available": True, "max_producible": max_producible}


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
    if batch.quantity_initial > 0:
        cost_loss = request.quantity * batch.unit_cost
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
