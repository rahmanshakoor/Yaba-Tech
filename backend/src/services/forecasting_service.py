"""Forecasting service using statsmodels ARIMA/SARIMA for demand prediction."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Item, ItemsInventory, ProductionLog


async def get_historical_usage(
    session: AsyncSession, item_id: int
) -> list[float]:
    """Fetch historical usage quantities for an item from ProductionLog.

    Returns daily aggregated usage as a time series.
    """
    result = await session.execute(
        select(
            func.date(ProductionLog.created_at).label("usage_date"),
            func.sum(ProductionLog.quantity_used).label("total_used"),
        )
        .join(
            ItemsInventory,
            ProductionLog.input_batch_id == ItemsInventory.batch_id,
        )
        .where(ItemsInventory.item_id == item_id)
        .group_by(func.date(ProductionLog.created_at))
        .order_by(func.date(ProductionLog.created_at))
    )
    rows = result.all()
    return [float(row.total_used) for row in rows]


def run_arima_forecast(
    usage_data: list[float], periods: int = 7
) -> list[float]:
    """Run ARIMA/SARIMA model on usage data and forecast future demand.

    Args:
        usage_data: Historical usage values (daily).
        periods: Number of periods (days) to forecast.

    Returns:
        List of predicted demand values.
    """
    if len(usage_data) < 3:
        # Not enough data for ARIMA; return average-based estimate
        avg = sum(usage_data) / len(usage_data) if usage_data else 0.0
        return [avg] * periods

    try:
        from statsmodels.tsa.arima.model import ARIMA

        model = ARIMA(usage_data, order=(1, 0, 0))
        fitted = model.fit()
        forecast = fitted.forecast(steps=periods)
        return [max(0.0, float(v)) for v in forecast]
    except Exception:
        # Fallback to simple average if ARIMA fails
        avg = sum(usage_data) / len(usage_data)
        return [avg] * periods


async def get_current_stock(
    session: AsyncSession, item_id: int
) -> float:
    """Get total current stock for an item."""
    result = await session.execute(
        select(func.coalesce(func.sum(ItemsInventory.quantity_current), 0.0)).where(
            ItemsInventory.item_id == item_id,
            ItemsInventory.quantity_current > 0,
        )
    )
    return float(result.scalar())


async def get_reorder_recommendations(
    session: AsyncSession,
    forecast_days: int = 7,
    threshold: float = 0.0,
) -> list[dict]:
    """Generate reorder recommendations based on predicted demand vs current stock.

    Args:
        session: Database session.
        forecast_days: Number of days to forecast.
        threshold: Minimum gap to trigger a recommendation.

    Returns:
        List of recommendation dicts.
    """
    # Get all raw items (these are the ones we purchase)
    result = await session.execute(select(Item))
    items = result.scalars().all()

    recommendations: list[dict] = []

    for item in items:
        usage_data = await get_historical_usage(session, item.item_id)

        if not usage_data:
            continue

        forecast = run_arima_forecast(usage_data, periods=forecast_days)
        predicted_demand = sum(forecast)
        current_stock = await get_current_stock(session, item.item_id)
        gap = predicted_demand - current_stock

        if gap > threshold:
            recommendations.append(
                {
                    "item_id": item.item_id,
                    "item_name": item.name,
                    "unit": item.unit,
                    "type": item.type,
                    "current_stock": current_stock,
                    "predicted_demand": round(predicted_demand, 2),
                    "gap": round(gap, 2),
                    "recommendation": f"We need {round(gap, 2)} {item.unit}s of {item.name}",
                }
            )

    return recommendations
