"""Production recording router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
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
        )
        return ProductionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
