"""Tests for inventory service."""

import pytest
from sqlalchemy import select

from src.models import Item, ItemComposition, ItemsInventory, ItemType, ProductionLog
from src.services.inventory_service import (
    check_ingredients_available,
    deduct_fifo,
    get_fifo_batches,
    get_item_stock,
)


@pytest.mark.asyncio
async def test_get_item_stock(db_session):
    """Test total stock calculation across batches."""
    item = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    db_session.add(item)
    await db_session.flush()

    batch1 = ItemsInventory(
        item_id=item.item_id, quantity_current=10.0, quantity_initial=10.0
    )
    batch2 = ItemsInventory(
        item_id=item.item_id, quantity_current=5.0, quantity_initial=5.0
    )
    # Empty batch should not be counted
    batch3 = ItemsInventory(
        item_id=item.item_id, quantity_current=0.0, quantity_initial=8.0
    )
    db_session.add_all([batch1, batch2, batch3])
    await db_session.commit()

    stock = await get_item_stock(db_session, item.item_id)
    assert stock == 15.0


@pytest.mark.asyncio
async def test_get_fifo_batches(db_session):
    """Test that batches are returned in FIFO order."""
    item = Item(name="Sugar", unit="kg", shelf_life_days=365, type=ItemType.RAW)
    db_session.add(item)
    await db_session.flush()

    batch1 = ItemsInventory(
        item_id=item.item_id, quantity_current=5.0, quantity_initial=5.0
    )
    batch2 = ItemsInventory(
        item_id=item.item_id, quantity_current=3.0, quantity_initial=3.0
    )
    db_session.add_all([batch1, batch2])
    await db_session.commit()

    batches = await get_fifo_batches(db_session, item.item_id)
    assert len(batches) == 2
    # First batch should have lower batch_id (created first)
    assert batches[0].batch_id < batches[1].batch_id


@pytest.mark.asyncio
async def test_check_ingredients_available_success(db_session):
    """Test successful ingredient availability check."""
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    cake = Item(name="Cake", unit="kg", shelf_life_days=3, type=ItemType.DISH)
    db_session.add_all([flour, cake])
    await db_session.flush()

    comp = ItemComposition(
        output_item_id=cake.item_id,
        input_item_id=flour.item_id,
        quantity_required=0.5,
    )
    db_session.add(comp)
    await db_session.flush()

    batch = ItemsInventory(
        item_id=flour.item_id, quantity_current=10.0, quantity_initial=10.0
    )
    db_session.add(batch)
    await db_session.commit()

    requirements = await check_ingredients_available(db_session, cake.item_id, 2.0)
    assert flour.item_id in requirements
    assert requirements[flour.item_id] == 1.0  # 0.5 * 2.0


@pytest.mark.asyncio
async def test_check_ingredients_insufficient(db_session):
    """Test ingredient check fails when stock is too low."""
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    cake = Item(name="Cake", unit="kg", shelf_life_days=3, type=ItemType.DISH)
    db_session.add_all([flour, cake])
    await db_session.flush()

    comp = ItemComposition(
        output_item_id=cake.item_id,
        input_item_id=flour.item_id,
        quantity_required=0.5,
    )
    db_session.add(comp)
    await db_session.flush()

    batch = ItemsInventory(
        item_id=flour.item_id, quantity_current=0.1, quantity_initial=10.0
    )
    db_session.add(batch)
    await db_session.commit()

    with pytest.raises(ValueError, match="Insufficient stock"):
        await check_ingredients_available(db_session, cake.item_id, 2.0)


@pytest.mark.asyncio
async def test_deduct_fifo(db_session):
    """Test FIFO deduction creates proper production logs."""
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    cake = Item(name="Cake", unit="kg", shelf_life_days=3, type=ItemType.DISH)
    db_session.add_all([flour, cake])
    await db_session.flush()

    batch1 = ItemsInventory(
        item_id=flour.item_id, quantity_current=3.0, quantity_initial=3.0
    )
    batch2 = ItemsInventory(
        item_id=flour.item_id, quantity_current=5.0, quantity_initial=5.0
    )
    output_batch = ItemsInventory(
        item_id=cake.item_id, quantity_current=1.0, quantity_initial=1.0
    )
    db_session.add_all([batch1, batch2, output_batch])
    await db_session.flush()

    flour_id = flour.item_id
    batch1_id = batch1.batch_id
    batch2_id = batch2.batch_id

    usage = await deduct_fifo(db_session, flour_id, 4.0, output_batch)
    await db_session.commit()

    assert len(usage) == 2
    assert usage[0]["quantity_used"] == 3.0  # batch1 fully consumed
    assert usage[1]["quantity_used"] == 1.0  # batch2 partially consumed

    # Re-fetch from DB to verify updated quantities
    result = await db_session.execute(
        select(ItemsInventory)
        .where(ItemsInventory.batch_id.in_([batch1_id, batch2_id]))
        .order_by(ItemsInventory.batch_id.asc())
    )
    refreshed = result.scalars().all()
    assert refreshed[0].quantity_current == 0.0
    assert refreshed[1].quantity_current == 4.0

    # Verify production logs created
    result = await db_session.execute(select(ProductionLog))
    logs = result.scalars().all()
    assert len(logs) == 2
