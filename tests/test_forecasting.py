"""Tests for forecasting service and ARIMA model."""

import pytest
from sqlalchemy import select

from src.models import Item, ItemComposition, ItemsInventory, ItemType, ProductionLog
from src.services.forecasting_service import (
    get_current_stock,
    get_historical_usage,
    get_reorder_recommendations,
    run_arima_forecast,
)


@pytest.mark.asyncio
async def test_arima_forecast_with_data():
    """Test that ARIMA model runs and returns predictions."""
    usage_data = [10.0, 12.0, 11.0, 13.0, 14.0, 12.0, 15.0, 13.0, 14.0, 16.0]
    forecast = run_arima_forecast(usage_data, periods=7)

    assert len(forecast) == 7
    assert all(v >= 0 for v in forecast)


@pytest.mark.asyncio
async def test_arima_forecast_insufficient_data():
    """Test fallback behavior with too little data for ARIMA."""
    usage_data = [10.0, 12.0]
    forecast = run_arima_forecast(usage_data, periods=7)

    assert len(forecast) == 7
    # Should return average-based estimate
    expected_avg = 11.0
    for v in forecast:
        assert abs(v - expected_avg) < 0.01


@pytest.mark.asyncio
async def test_arima_forecast_empty_data():
    """Test forecast with empty data."""
    forecast = run_arima_forecast([], periods=5)
    assert len(forecast) == 5
    assert all(v == 0.0 for v in forecast)


@pytest.mark.asyncio
async def test_get_current_stock(db_session):
    """Test getting current stock for an item."""
    item = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    db_session.add(item)
    await db_session.flush()

    batch1 = ItemsInventory(
        item_id=item.item_id, quantity_current=10.0, quantity_initial=20.0
    )
    batch2 = ItemsInventory(
        item_id=item.item_id, quantity_current=5.0, quantity_initial=10.0
    )
    db_session.add_all([batch1, batch2])
    await db_session.commit()

    stock = await get_current_stock(db_session, item.item_id)
    assert stock == 15.0


@pytest.mark.asyncio
async def test_get_historical_usage(db_session):
    """Test fetching historical usage from production logs."""
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    cake = Item(name="Cake", unit="kg", shelf_life_days=3, type=ItemType.DISH)
    db_session.add_all([flour, cake])
    await db_session.flush()

    input_batch = ItemsInventory(
        item_id=flour.item_id, quantity_current=50.0, quantity_initial=50.0
    )
    output_batch = ItemsInventory(
        item_id=cake.item_id, quantity_current=10.0, quantity_initial=10.0
    )
    db_session.add_all([input_batch, output_batch])
    await db_session.flush()

    log = ProductionLog(
        output_batch_id=output_batch.batch_id,
        input_batch_id=input_batch.batch_id,
        quantity_used=5.0,
    )
    db_session.add(log)
    await db_session.commit()

    usage = await get_historical_usage(db_session, flour.item_id)
    assert len(usage) >= 1
    assert usage[0] == 5.0


@pytest.mark.asyncio
async def test_reorder_recommendations(db_session):
    """Test generating reorder recommendations with mock history."""
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    cake = Item(name="Cake", unit="kg", shelf_life_days=3, type=ItemType.DISH)
    db_session.add_all([flour, cake])
    await db_session.flush()

    # Add some stock
    input_batch = ItemsInventory(
        item_id=flour.item_id, quantity_current=2.0, quantity_initial=50.0
    )
    output_batch = ItemsInventory(
        item_id=cake.item_id, quantity_current=10.0, quantity_initial=10.0
    )
    db_session.add_all([input_batch, output_batch])
    await db_session.flush()

    # Add usage history
    log = ProductionLog(
        output_batch_id=output_batch.batch_id,
        input_batch_id=input_batch.batch_id,
        quantity_used=10.0,
    )
    db_session.add(log)
    await db_session.commit()

    recommendations = await get_reorder_recommendations(
        db_session, forecast_days=7, threshold=0.0
    )

    # Flour should appear in recommendations since stock (2.0) < predicted demand
    flour_recs = [r for r in recommendations if r["item_name"] == "Flour"]
    assert len(flour_recs) == 1
    assert flour_recs[0]["current_stock"] == 2.0
    assert flour_recs[0]["gap"] > 0
