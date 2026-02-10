"""Inventory service with FIFO batch selection logic."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Item,
    ItemComposition,
    ItemsInventory,
    ProductionLog,
)
from src.services.cost_service import calculate_recipe_cost


async def get_item_stock(session: AsyncSession, item_id: int) -> float:
    """Get total current stock for an item across all batches."""
    result = await session.execute(
        select(ItemsInventory).where(
            ItemsInventory.item_id == item_id,
            ItemsInventory.quantity_current > 0,
        )
    )
    batches = result.scalars().all()
    return sum(b.quantity_current for b in batches)


async def get_fifo_batches(
    session: AsyncSession, item_id: int
) -> list[ItemsInventory]:
    """Get batches for an item ordered by FIFO (oldest first)."""
    result = await session.execute(
        select(ItemsInventory)
        .where(
            ItemsInventory.item_id == item_id,
            ItemsInventory.quantity_current > 0,
        )
        .order_by(ItemsInventory.created_at.asc(), ItemsInventory.batch_id.asc())
    )
    return list(result.scalars().all())


async def check_ingredients_available(
    session: AsyncSession,
    output_item_id: int,
    quantity_to_produce: float,
    manual_batches: dict[int, int] | None = None,
) -> dict[int, float]:
    """Check if all ingredients are available for production.

    Returns:
        Dict mapping input_item_id -> quantity_needed.

    Raises:
        ValueError: If any ingredient has insufficient stock.
    """
    # Get recipe (compositions) for the output item
    result = await session.execute(
        select(ItemComposition).where(
            ItemComposition.output_item_id == output_item_id
        )
    )
    compositions = result.scalars().all()

    if not compositions:
        raise ValueError(
            f"No recipe found for item_id={output_item_id}"
        )

    requirements: dict[int, float] = {}
    for comp in compositions:
        needed = comp.quantity_required * quantity_to_produce
        # If manual batch is specified for this ingredient, verify it content
        if manual_batches and comp.input_item_id in manual_batches:
            batch_id = manual_batches[comp.input_item_id]
            batch_result = await session.execute(
                select(ItemsInventory).where(
                    ItemsInventory.batch_id == batch_id,
                    ItemsInventory.item_id == comp.input_item_id,
                )
            )
            batch = batch_result.scalar_one_or_none()
            
            if not batch:
                raise ValueError(f"Selected batch {batch_id} not found for item {comp.input_item_id}")
            
            if batch.quantity_current < needed:
                 max_possible = int(batch.quantity_current / comp.quantity_required)
                 raise ValueError(
                    f"Batch {batch_id} has insufficient quantity ({batch.quantity_current}). "
                    f"Max possible to produce: {max_possible}"
                )
        else:
            stock = await get_item_stock(session, comp.input_item_id)
            if stock < needed:
                # Calculate max possible for this ingredient
                max_possible = int(stock / comp.quantity_required)
                
                # Get item name for better error message
                item_result = await session.execute(
                    select(Item).where(Item.item_id == comp.input_item_id)
                )
                item = item_result.scalar_one_or_none()
                item_name = item.name if item else f"item_id={comp.input_item_id}"
                
                raise ValueError(
                    f"Insufficient stock for '{item_name}': "
                    f"need {needed}, have {stock}. "
                    f"Max possible to produce: {max_possible}"
                )
        requirements[comp.input_item_id] = needed

    return requirements


async def deduct_fifo(
    session: AsyncSession,
    item_id: int,
    quantity_needed: float,
    output_batch: ItemsInventory,
) -> list[dict]:
    """Deduct quantity from batches using FIFO order.

    Returns:
        List of dicts describing which batches were used and how much.
    """
    batches = await get_fifo_batches(session, item_id)
    remaining = quantity_needed
    usage_log: list[dict] = []

    for batch in batches:
        if remaining <= 0:
            break

        deduct = min(batch.quantity_current, remaining)
        batch.quantity_current -= deduct
        remaining -= deduct

        # Create production log entry
        log_entry = ProductionLog(
            output_batch_id=output_batch.batch_id,
            input_batch_id=batch.batch_id,
            quantity_used=deduct,
        )
        session.add(log_entry)

        usage_log.append(
            {
                "input_batch_id": batch.batch_id,
                "item_id": item_id,
                "quantity_used": deduct,
            }
        )

    return usage_log


async def deduct_manual(
    session: AsyncSession,
    item_id: int,
    quantity_needed: float,
    batch_id: int,
    output_batch: ItemsInventory,
) -> list[dict]:
    """Deduct quantity from a specific batch."""
    result = await session.execute(
        select(ItemsInventory).where(ItemsInventory.batch_id == batch_id)
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise ValueError(f"Batch {batch_id} not found")
        
    # We already validated quantity in check_ingredients_available, but safe to check again or just do it
    if batch.quantity_current < quantity_needed:
         raise ValueError(f"Batch {batch_id} insufficient stock")

    batch.quantity_current -= quantity_needed
    
    # Create production log entry
    log_entry = ProductionLog(
        output_batch_id=output_batch.batch_id,
        input_batch_id=batch.batch_id,
        quantity_used=quantity_needed,
    )
    session.add(log_entry)

    return [
        {
            "input_batch_id": batch.batch_id,
            "item_id": item_id,
            "quantity_used": quantity_needed,
        }
    ]


async def produce_item(
    session: AsyncSession,
    output_item_id: int,
    quantity_to_produce: float,
    manual_batches: dict[int, int] | None = None,
) -> dict:
    """Execute a production run: validate, deduct ingredients, create output batch.

    Returns:
        Dict with production details.

    Raises:
        ValueError: If ingredients are insufficient or recipe not found.
    """
    # 1. Validate ingredients
    requirements = await check_ingredients_available(
        session, output_item_id, quantity_to_produce, manual_batches
    )

    # 2. Get the output item for shelf life calculation
    item_result = await session.execute(
        select(Item).where(Item.item_id == output_item_id)
    )
    output_item = item_result.scalar_one_or_none()
    if not output_item:
        raise ValueError(f"Output item_id={output_item_id} not found")

    # 3. Create the output batch
    expiration = None
    if output_item.shelf_life_days > 0:
        expiration = datetime.now(timezone.utc) + timedelta(
            days=output_item.shelf_life_days
        )

    # Calculate the recipe cost for this production batch
    recipe_cost = await calculate_recipe_cost(session, output_item_id)

    output_batch = ItemsInventory(
        item_id=output_item_id,
        quantity_current=quantity_to_produce,
        quantity_initial=quantity_to_produce,
        unit_cost=recipe_cost,
        expiration_date=expiration,
    )
    session.add(output_batch)
    await session.flush()  # Get the batch_id

    # 4. Deduct ingredients using FIFO
    all_usage: list[dict] = []
    for input_item_id, qty_needed in requirements.items():
        if manual_batches and input_item_id in manual_batches:
             usage = await deduct_manual(
                session, 
                input_item_id, 
                qty_needed, 
                manual_batches[input_item_id],
                output_batch
            )
        else:
            usage = await deduct_fifo(
                session, input_item_id, qty_needed, output_batch
            )
        all_usage.extend(usage)

    await session.commit()

    # Update average_cost on the output item
    output_item.average_cost = recipe_cost
    await session.commit()

    return {
        "output_batch_id": output_batch.batch_id,
        "output_item_id": output_item_id,
        "quantity_produced": quantity_to_produce,
        "ingredients_used": all_usage,
    }
