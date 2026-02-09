"""Forecasting router for reorder recommendations."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas import ForecastingResponse
from src.services.forecasting_service import get_reorder_recommendations

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


@router.get("/reorder-recommendations", response_model=ForecastingResponse)
async def reorder_recommendations(
    forecast_days: int = Query(default=7, ge=1, le=90),
    threshold: float = Query(default=0.0, ge=0.0),
    db: AsyncSession = Depends(get_db),
):
    """Get reorder recommendations based on demand forecasting."""
    recommendations = await get_reorder_recommendations(
        db, forecast_days=forecast_days, threshold=threshold
    )
    return ForecastingResponse(
        recommendations=[
            {
                "item_id": r["item_id"],
                "item_name": r["item_name"],
                "current_stock": r["current_stock"],
                "predicted_demand": r["predicted_demand"],
                "gap": r["gap"],
                "recommendation": r["recommendation"],
            }
            for r in recommendations
        ]
    )
