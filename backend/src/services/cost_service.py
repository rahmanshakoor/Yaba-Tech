"""Cost calculation service for inventory items."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Item, ItemComposition, ItemsInventory


async def calculate_moving_average(
    session: AsyncSession,
    item_id: int,
    new_quantity: float,
    new_unit_cost: float,
) -> float:
    """Calculate weighted moving average cost for a raw item.

    Formula: ((CurrentTotalQty * CurrentAvgCost) + (NewQty * NewPrice))
             / (CurrentTotalQty + NewQty)

    Args:
        session: Async database session.
        item_id: The raw item ID.
        new_quantity: Quantity being added (from invoice).
        new_unit_cost: Unit cost from the invoice line item.

    Returns:
        The updated average cost.
    """
    result = await session.execute(
        select(Item).where(Item.item_id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise ValueError(f"Item with id={item_id} not found")

    # Get current total stock across all batches
    batches_result = await session.execute(
        select(ItemsInventory).where(
            ItemsInventory.item_id == item_id,
            ItemsInventory.quantity_current > 0,
        )
    )
    batches = batches_result.scalars().all()
    current_total_qty = sum(b.quantity_current for b in batches)
    current_avg_cost = item.average_cost or 0.0

    total_qty = current_total_qty + new_quantity
    if total_qty > 0:
        new_avg = (
            (current_total_qty * current_avg_cost)
            + (new_quantity * new_unit_cost)
        ) / total_qty
    else:
        new_avg = new_unit_cost

    item.average_cost = new_avg
    return new_avg


async def calculate_recipe_cost(
    session: AsyncSession,
    item_id: int,
    _visited: set[int] | None = None,
) -> float:
    """Recursively calculate cost of a prepped/dish item from its recipe.

    For raw items (no recipe), returns the item's average_cost.
    For composed items, sums (ingredient_cost * quantity_required).

    Args:
        session: Async database session.
        item_id: The item ID to calculate cost for.
        _visited: Internal set to detect circular recipes.

    Returns:
        The total cost per unit of the item.
    """
    if _visited is None:
        _visited = set()

    if item_id in _visited:
        return 0.0  # Prevent infinite recursion on circular recipes
    _visited.add(item_id)

    # Check if the item has a recipe
    result = await session.execute(
        select(ItemComposition).where(
            ItemComposition.output_item_id == item_id
        )
    )
    recipe = result.scalars().all()

    if not recipe:
        # It's a raw item — return its average_cost
        item_result = await session.execute(
            select(Item).where(Item.item_id == item_id)
        )
        item = item_result.scalar_one_or_none()
        return item.average_cost if item else 0.0

    total_cost = 0.0
    for ingredient in recipe:
        ing_cost = await calculate_recipe_cost(
            session, ingredient.input_item_id, _visited
        )
        total_cost += ing_cost * ingredient.quantity_required

    return total_cost
