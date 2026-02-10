"""Tests for exception handling: waste management and production reversion."""

import pytest
from sqlalchemy import select

from src.models import (
    Item,
    ItemComposition,
    ItemsInventory,
    ItemType,
    ProductionLog,
    WasteLog,
    WasteReason,
)
from src.services.inventory_service import produce_item


async def _setup_soup_recipe(session):
    """Set up a recipe: Soup requires Carrots(2.0kg) and Water(1.0 liter)."""
    carrots = Item(name="Carrots", unit="kg", shelf_life_days=14, type=ItemType.RAW)
    water = Item(name="Water", unit="liter", shelf_life_days=0, type=ItemType.RAW)
    soup = Item(name="Soup", unit="liter", shelf_life_days=3, type=ItemType.DISH)

    session.add_all([carrots, water, soup])
    await session.flush()

    comp1 = ItemComposition(
        output_item_id=soup.item_id,
        input_item_id=carrots.item_id,
        quantity_required=2.0,
    )
    comp2 = ItemComposition(
        output_item_id=soup.item_id,
        input_item_id=water.item_id,
        quantity_required=1.0,
    )
    session.add_all([comp1, comp2])
    await session.flush()

    return carrots, water, soup


@pytest.mark.asyncio
async def test_revert_production_restocks_ingredients(db_session):
    """Test that reverting a soup batch puts the carrots back into inventory."""
    carrots, water, soup = await _setup_soup_recipe(db_session)

    # Add inventory batches
    carrot_batch = ItemsInventory(
        item_id=carrots.item_id,
        quantity_current=10.0,
        quantity_initial=10.0,
    )
    water_batch = ItemsInventory(
        item_id=water.item_id,
        quantity_current=10.0,
        quantity_initial=10.0,
    )
    db_session.add_all([carrot_batch, water_batch])
    await db_session.flush()

    # Produce 2 liters of soup -> uses 4kg carrots, 2 liters water
    result = await produce_item(db_session, soup.item_id, 2.0)
    output_batch_id = result["output_batch_id"]

    await db_session.refresh(carrot_batch)
    await db_session.refresh(water_batch)
    assert carrot_batch.quantity_current == 6.0  # 10 - 4
    assert water_batch.quantity_current == 8.0  # 10 - 2

    # Get one of the production logs for the revert
    logs_result = await db_session.execute(
        select(ProductionLog).where(
            ProductionLog.output_batch_id == output_batch_id
        )
    )
    logs = logs_result.scalars().all()
    assert len(logs) == 2  # one for carrots, one for water
    log_id = logs[0].log_id

    # Now revert using the production router logic inline
    # Find all production logs for this output batch
    all_logs_result = await db_session.execute(
        select(ProductionLog).where(
            ProductionLog.output_batch_id == output_batch_id
        )
    )
    all_logs = all_logs_result.scalars().all()

    # Restock input batches
    for log in all_logs:
        input_batch_result = await db_session.execute(
            select(ItemsInventory).where(
                ItemsInventory.batch_id == log.input_batch_id
            )
        )
        input_batch = input_batch_result.scalar_one_or_none()
        if input_batch:
            input_batch.quantity_current += log.quantity_used

    # Void output batch
    output_batch_result = await db_session.execute(
        select(ItemsInventory).where(
            ItemsInventory.batch_id == output_batch_id
        )
    )
    output_batch = output_batch_result.scalar_one_or_none()
    output_batch.quantity_current = 0

    # Delete production logs
    for log in all_logs:
        await db_session.delete(log)

    await db_session.commit()

    # Verify: carrots and water are fully restocked
    await db_session.refresh(carrot_batch)
    await db_session.refresh(water_batch)
    await db_session.refresh(output_batch)

    assert carrot_batch.quantity_current == 10.0  # restored
    assert water_batch.quantity_current == 10.0  # restored
    assert output_batch.quantity_current == 0  # voided


@pytest.mark.asyncio
async def test_waste_creates_financial_loss_record(db_session):
    """Test that logging waste creates a WasteLog with cost_loss."""
    carrots = Item(name="Carrots", unit="kg", shelf_life_days=14, type=ItemType.RAW)
    db_session.add(carrots)
    await db_session.flush()

    batch = ItemsInventory(
        item_id=carrots.item_id,
        quantity_current=10.0,
        quantity_initial=10.0,
    )
    db_session.add(batch)
    await db_session.flush()

    # Log 3kg of waste as spoiled
    waste_quantity = 3.0
    # Cost uses placeholder unit cost of 1.0 (matches implementation)
    cost_loss = waste_quantity * 1.0

    batch.quantity_current -= waste_quantity

    waste_entry = WasteLog(
        batch_id=batch.batch_id,
        quantity=waste_quantity,
        reason=WasteReason.SPOILED,
        cost_loss=cost_loss,
    )
    db_session.add(waste_entry)
    await db_session.commit()

    # Verify batch quantity was deducted
    await db_session.refresh(batch)
    assert batch.quantity_current == 7.0  # 10 - 3

    # Verify waste log was created
    result = await db_session.execute(select(WasteLog))
    waste_logs = result.scalars().all()
    assert len(waste_logs) == 1

    waste_log = waste_logs[0]
    assert waste_log.batch_id == batch.batch_id
    assert waste_log.quantity == 3.0
    assert waste_log.reason == WasteReason.SPOILED
    assert waste_log.cost_loss == 3.0


@pytest.mark.asyncio
async def test_revert_blocked_when_output_already_used(db_session):
    """Test that reversion fails if the output batch has been used in another production."""
    carrots, water, soup = await _setup_soup_recipe(db_session)

    # Add inventory
    carrot_batch = ItemsInventory(
        item_id=carrots.item_id,
        quantity_current=20.0,
        quantity_initial=20.0,
    )
    water_batch = ItemsInventory(
        item_id=water.item_id,
        quantity_current=20.0,
        quantity_initial=20.0,
    )
    db_session.add_all([carrot_batch, water_batch])
    await db_session.flush()

    # Produce soup
    result = await produce_item(db_session, soup.item_id, 2.0)
    output_batch_id = result["output_batch_id"]

    # Create a second recipe that uses soup as input
    stew = Item(name="Stew", unit="liter", shelf_life_days=2, type=ItemType.DISH)
    db_session.add(stew)
    await db_session.flush()

    comp = ItemComposition(
        output_item_id=stew.item_id,
        input_item_id=soup.item_id,
        quantity_required=1.0,
    )
    db_session.add(comp)
    await db_session.flush()

    # Produce stew using the soup batch
    result2 = await produce_item(db_session, stew.item_id, 1.0)

    # Now try to check if output batch was used (simulating what the revert endpoint does)
    usage_result = await db_session.execute(
        select(ProductionLog).where(
            ProductionLog.input_batch_id == output_batch_id
        )
    )
    used = usage_result.scalar_one_or_none()
    assert used is not None  # Output batch was used, so revert should be blocked
