"""Tests for database models and relationships."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.models import (
    Invoice,
    Item,
    ItemComposition,
    ItemsInventory,
    ItemType,
    ProductionLog,
)


@pytest.mark.asyncio
async def test_create_item(db_session):
    """Test creating an Item record."""
    item = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    db_session.add(item)
    await db_session.commit()

    result = await db_session.execute(select(Item).where(Item.name == "Flour"))
    fetched = result.scalar_one()
    assert fetched.name == "Flour"
    assert fetched.unit == "kg"
    assert fetched.type == ItemType.RAW
    assert fetched.shelf_life_days == 180


@pytest.mark.asyncio
async def test_item_types(db_session):
    """Test all item types can be created."""
    for item_type in ItemType:
        item = Item(
            name=f"Test_{item_type.value}",
            unit="kg",
            shelf_life_days=30,
            type=item_type,
        )
        db_session.add(item)
    await db_session.commit()

    result = await db_session.execute(select(Item))
    items = result.scalars().all()
    assert len(items) == 3


@pytest.mark.asyncio
async def test_item_composition_relationship(db_session):
    """Test the recipe/BOM relationship between items."""
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    sugar = Item(name="Sugar", unit="kg", shelf_life_days=365, type=ItemType.RAW)
    cake = Item(name="Cake", unit="kg", shelf_life_days=3, type=ItemType.DISH)

    db_session.add_all([flour, sugar, cake])
    await db_session.flush()

    comp1 = ItemComposition(
        output_item_id=cake.item_id,
        input_item_id=flour.item_id,
        quantity_required=0.5,
    )
    comp2 = ItemComposition(
        output_item_id=cake.item_id,
        input_item_id=sugar.item_id,
        quantity_required=0.2,
    )
    db_session.add_all([comp1, comp2])
    await db_session.commit()

    result = await db_session.execute(
        select(ItemComposition).where(ItemComposition.output_item_id == cake.item_id)
    )
    compositions = result.scalars().all()
    assert len(compositions) == 2


@pytest.mark.asyncio
async def test_unique_item_name(db_session):
    """Test that duplicate item names are rejected."""
    item1 = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    db_session.add(item1)
    await db_session.commit()

    item2 = Item(name="Flour", unit="lb", shelf_life_days=90, type=ItemType.RAW)
    db_session.add(item2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_inventory_batch(db_session):
    """Test creating inventory batch records."""
    item = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    db_session.add(item)
    await db_session.flush()

    batch = ItemsInventory(
        item_id=item.item_id,
        quantity_current=50.0,
        quantity_initial=50.0,
    )
    db_session.add(batch)
    await db_session.commit()

    result = await db_session.execute(
        select(ItemsInventory).where(ItemsInventory.item_id == item.item_id)
    )
    fetched = result.scalar_one()
    assert fetched.quantity_current == 50.0
    assert fetched.quantity_initial == 50.0


@pytest.mark.asyncio
async def test_production_log(db_session):
    """Test creating production log entries."""
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

    result = await db_session.execute(select(ProductionLog))
    fetched = result.scalar_one()
    assert fetched.quantity_used == 5.0
    assert fetched.output_batch_id == output_batch.batch_id
    assert fetched.input_batch_id == input_batch.batch_id


@pytest.mark.asyncio
async def test_invoice_with_inventory(db_session):
    """Test invoice -> inventory relationship."""
    invoice = Invoice(
        supplier_name="Test Supplier", total_cost=500.0, image_url="s3://test"
    )
    db_session.add(invoice)
    await db_session.flush()

    item = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    db_session.add(item)
    await db_session.flush()

    batch = ItemsInventory(
        item_id=item.item_id,
        quantity_current=50.0,
        quantity_initial=50.0,
        source_invoice_id=invoice.invoice_id,
    )
    db_session.add(batch)
    await db_session.commit()

    result = await db_session.execute(
        select(ItemsInventory).where(
            ItemsInventory.source_invoice_id == invoice.invoice_id
        )
    )
    fetched = result.scalar_one()
    assert fetched.source_invoice_id == invoice.invoice_id


@pytest.mark.asyncio
async def test_cascade_delete_item_removes_compositions(db_session):
    """Test that deleting an item cascades to its compositions as output."""
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
    await db_session.commit()

    # Delete the cake (output item) - should cascade delete its compositions
    await db_session.delete(cake)
    await db_session.commit()

    result = await db_session.execute(select(ItemComposition))
    remaining = result.scalars().all()
    assert len(remaining) == 0
