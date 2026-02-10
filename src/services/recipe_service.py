"""Recipe service for managing item compositions."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Item, ItemComposition, ItemType


async def save_composition(
    session: AsyncSession,
    target_item_id: int,
    ingredients: list[dict],
) -> list[ItemComposition]:
    """Save a full composition (recipe) for a target item.

    Args:
        session: Async database session.
        target_item_id: The item being defined (output).
        ingredients: List of dicts with 'input_item_id' and 'quantity'.

    Returns:
        List of created ItemComposition rows.

    Raises:
        ValueError: If the target item is not found or validation fails.
    """
    # 1. Fetch the target item
    result = await session.execute(
        select(Item).where(Item.item_id == target_item_id)
    )
    target_item = result.scalar_one_or_none()
    if not target_item:
        raise ValueError(f"Target item with id={target_item_id} not found")

    if target_item.type == ItemType.RAW:
        raise ValueError("Raw items cannot have compositions")

    # 2. Fetch all input items
    input_ids = [ing["input_item_id"] for ing in ingredients]
    input_result = await session.execute(
        select(Item).where(Item.item_id.in_(input_ids))
    )
    input_items = {item.item_id: item for item in input_result.scalars().all()}

    # Verify all input items exist
    missing = set(input_ids) - set(input_items.keys())
    if missing:
        raise ValueError(f"Input items not found: {missing}")

    # 3. Validate input item types based on target type
    if target_item.type == ItemType.PREPPED:
        # Validation Rule A: Prepped items can only use Raw ingredients
        invalid = [
            iid for iid in input_ids if input_items[iid].type != ItemType.RAW
        ]
        if invalid:
            invalid_names = [input_items[iid].name for iid in invalid]
            raise ValueError(
                f"Prepped items can only use Raw ingredients. "
                f"Invalid: {invalid_names}"
            )

    elif target_item.type == ItemType.DISH:
        # Validation Rule B: Dish items can use Raw or Prepped ingredients
        allowed = {ItemType.RAW, ItemType.PREPPED}
        invalid = [
            iid for iid in input_ids if input_items[iid].type not in allowed
        ]
        if invalid:
            invalid_names = [input_items[iid].name for iid in invalid]
            raise ValueError(
                f"Dish items can only use Raw or Prepped ingredients. "
                f"Invalid: {invalid_names}"
            )

    # 4. Clear existing compositions for this target item
    await session.execute(
        delete(ItemComposition).where(
            ItemComposition.output_item_id == target_item_id
        )
    )

    # 5. Bulk insert new compositions
    new_compositions = []
    for ing in ingredients:
        comp = ItemComposition(
            output_item_id=target_item_id,
            input_item_id=ing["input_item_id"],
            quantity_required=ing["quantity"],
        )
        session.add(comp)
        new_compositions.append(comp)

    await session.flush()
    return new_compositions
