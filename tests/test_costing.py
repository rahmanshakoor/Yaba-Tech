"""Tests for cost calculation service — roll-up costing logic."""

import pytest

from src.models import Item, ItemComposition, ItemsInventory, ItemType
from src.services.cost_service import calculate_moving_average, calculate_recipe_cost


@pytest.mark.asyncio
async def test_pizza_rollup_cost(db_session):
    """Verify recursive roll-up cost: Pizza = 0.5kg Dough + 0.2kg Cheese.

    Dough costs $1/kg, Cheese costs $10/kg.
    Expected Pizza cost = (0.5 * 1) + (0.2 * 10) = $2.50.
    """
    # 1. Create raw items
    dough = Item(name="Dough", unit="kg", shelf_life_days=7, type=ItemType.RAW)
    cheese = Item(name="Cheese", unit="kg", shelf_life_days=14, type=ItemType.RAW)
    db_session.add_all([dough, cheese])
    await db_session.flush()

    # 2. Set average costs via moving average (called before batch creation, as in invoice flow)
    await calculate_moving_average(db_session, dough.item_id, 10.0, 1.0)
    await calculate_moving_average(db_session, cheese.item_id, 5.0, 10.0)

    dough_batch = ItemsInventory(
        item_id=dough.item_id,
        quantity_current=10.0,
        quantity_initial=10.0,
        unit_cost=1.0,
    )
    cheese_batch = ItemsInventory(
        item_id=cheese.item_id,
        quantity_current=5.0,
        quantity_initial=5.0,
        unit_cost=10.0,
    )
    db_session.add_all([dough_batch, cheese_batch])
    await db_session.commit()

    # Verify average costs are set
    assert dough.average_cost == pytest.approx(1.0)
    assert cheese.average_cost == pytest.approx(10.0)

    # 3. Create Dish "Pizza" with recipe
    pizza = Item(name="Pizza", unit="unit", shelf_life_days=1, type=ItemType.DISH)
    db_session.add(pizza)
    await db_session.flush()

    comp_dough = ItemComposition(
        output_item_id=pizza.item_id,
        input_item_id=dough.item_id,
        quantity_required=0.5,
    )
    comp_cheese = ItemComposition(
        output_item_id=pizza.item_id,
        input_item_id=cheese.item_id,
        quantity_required=0.2,
    )
    db_session.add_all([comp_dough, comp_cheese])
    await db_session.commit()

    # 4. Calculate and assert recipe cost
    cost = await calculate_recipe_cost(db_session, pizza.item_id)
    assert cost == pytest.approx(2.50)


@pytest.mark.asyncio
async def test_moving_average_cost(db_session):
    """Test weighted moving average cost calculation."""
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    db_session.add(flour)
    await db_session.flush()

    # First purchase: 10kg at $2/kg (moving average calculated before batch creation)
    avg = await calculate_moving_average(db_session, flour.item_id, 10.0, 2.0)
    assert avg == pytest.approx(2.0)

    batch1 = ItemsInventory(
        item_id=flour.item_id,
        quantity_current=10.0,
        quantity_initial=10.0,
        unit_cost=2.0,
    )
    db_session.add(batch1)
    await db_session.flush()

    # Second purchase: 5kg at $4/kg
    avg = await calculate_moving_average(db_session, flour.item_id, 5.0, 4.0)

    batch2 = ItemsInventory(
        item_id=flour.item_id,
        quantity_current=5.0,
        quantity_initial=5.0,
        unit_cost=4.0,
    )
    db_session.add(batch2)
    await db_session.flush()
    expected = (10 * 2.0 + 5 * 4.0) / (10 + 5)
    assert avg == pytest.approx(expected, rel=1e-2)


@pytest.mark.asyncio
async def test_nested_recipe_cost(db_session):
    """Test recursive cost through multiple levels: Dish uses Prepped, Prepped uses Raw."""
    # Raw items
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    sugar = Item(name="Sugar", unit="kg", shelf_life_days=365, type=ItemType.RAW)
    db_session.add_all([flour, sugar])
    await db_session.flush()

    # Set average costs
    flour.average_cost = 2.0
    sugar.average_cost = 3.0

    # Prepped item: "Dough" uses 1kg Flour + 0.5kg Sugar
    dough = Item(name="Dough", unit="kg", shelf_life_days=3, type=ItemType.PREPPED)
    db_session.add(dough)
    await db_session.flush()

    db_session.add_all([
        ItemComposition(output_item_id=dough.item_id, input_item_id=flour.item_id, quantity_required=1.0),
        ItemComposition(output_item_id=dough.item_id, input_item_id=sugar.item_id, quantity_required=0.5),
    ])
    await db_session.flush()

    # Dish: "Cake" uses 2kg Dough
    cake = Item(name="Cake", unit="unit", shelf_life_days=2, type=ItemType.DISH)
    db_session.add(cake)
    await db_session.flush()

    db_session.add(
        ItemComposition(output_item_id=cake.item_id, input_item_id=dough.item_id, quantity_required=2.0)
    )
    await db_session.commit()

    # Dough cost = (1 * 2.0) + (0.5 * 3.0) = 3.5
    dough_cost = await calculate_recipe_cost(db_session, dough.item_id)
    assert dough_cost == pytest.approx(3.5)

    # Cake cost = 2 * 3.5 = 7.0
    cake_cost = await calculate_recipe_cost(db_session, cake.item_id)
    assert cake_cost == pytest.approx(7.0)
