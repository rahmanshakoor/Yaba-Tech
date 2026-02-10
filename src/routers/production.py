"""Production recording router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import ItemsInventory, ProductionLog
from src.schemas import ProductionRequest, ProductionResponse
from src.services.inventory_service import produce_item

router = APIRouter(prefix="/production", tags=["production"])


@router.post("/record", response_model=ProductionResponse)
async def record_production(
    request: ProductionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Record a production run: deduct ingredients via FIFO and create output batch."""
    try:
        result = await produce_item(
            db,
            output_item_id=request.output_item_id,
            quantity_to_produce=request.quantity_to_produce,
            manual_batches=request.manual_batches,
        )
        return ProductionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{log_id}/revert")
async def revert_production(
    log_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Revert a production run: restock input ingredients and void the output batch."""
    # Find the production log entry
    result = await db.execute(
        select(ProductionLog).where(ProductionLog.log_id == log_id)
    )
    log_entry = result.scalar_one_or_none()
    if not log_entry:
        raise HTTPException(status_code=404, detail="Production log not found")

    output_batch_id = log_entry.output_batch_id

    # Check if the output batch has been used as input in another production
    usage_result = await db.execute(
        select(ProductionLog).where(
            ProductionLog.input_batch_id == output_batch_id
        )
    )
    if usage_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Cannot revert; item already used in another dish.",
        )

    # Find all production logs for this output batch (there may be multiple inputs)
    all_logs_result = await db.execute(
        select(ProductionLog).where(
            ProductionLog.output_batch_id == output_batch_id
        )
    )
    all_logs = all_logs_result.scalars().all()

    # Restock: add quantity_used back to each input batch
    for log in all_logs:
        input_batch_result = await db.execute(
            select(ItemsInventory).where(
                ItemsInventory.batch_id == log.input_batch_id
            )
        )
        input_batch = input_batch_result.scalar_one_or_none()
        if input_batch:
            input_batch.quantity_current += log.quantity_used

    # Void: set output batch quantity to 0
    output_batch_result = await db.execute(
        select(ItemsInventory).where(
            ItemsInventory.batch_id == output_batch_id
        )
    )
    output_batch = output_batch_result.scalar_one_or_none()
    if output_batch:
        output_batch.quantity_current = 0

    # Delete the production log entries
    for log in all_logs:
        await db.delete(log)

    await db.commit()
    return {"detail": "Production reverted", "log_id": log_id}
