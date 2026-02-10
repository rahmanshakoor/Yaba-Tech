"""
Seed script for the YABA database.

Populates the database with a realistic "Italian Bistro" kitchen scenario
spanning the last 30 days so that graphs and forecasts appear immediately.

Usage:
    python scripts/seed_data.py
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Resolve project root so that imports from `src/` work regardless of cwd.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from models import (  # noqa: E402
    Base,
    Invoice,
    Item,
    ItemComposition,
    ItemsInventory,
    ItemType,
    ProductionLog,
    WasteLog,
    WasteReason,
)

DATABASE_URL = "sqlite+aiosqlite:///./yaba.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── helpers ----------------------------------------------------------------

def _log(msg: str) -> None:
    print(f"[SEED] {msg}")


def _daily_pizza_count(day_offset: int) -> int:
    """Return a slightly randomised production count.

    Weekends (Sat/Sun) are busier than weekdays.
    """
    target_date = datetime.now() + timedelta(days=day_offset)
    weekday = target_date.weekday()  # 0=Mon … 6=Sun
    if weekday >= 5:  # weekend
        return random.randint(35, 50)
    return random.randint(20, 35)


# ── Step 1: Clean Slate ----------------------------------------------------

async def wipe_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    _log("Database wiped clean.")


# ── Step 2: Master Data (The Menu) -----------------------------------------

async def create_items(session: AsyncSession) -> dict[str, Item]:
    """Create Item definitions and return a name→Item mapping."""

    definitions = [
        # Raw Ingredients
        ("00 Flour", "Kg", 365, ItemType.RAW),
        ("San Marzano Tomatoes", "Can", 730, ItemType.RAW),
        ("Mozzarella Cheese", "Kg", 14, ItemType.RAW),
        ("Fresh Basil", "Bunch", 4, ItemType.RAW),
        # Prepped Items
        ("Pizza Dough", "Ball", 3, ItemType.PREPPED),
        ("Pizza Sauce", "Liter", 5, ItemType.PREPPED),
        # Dishes
        ("Margherita Pizza", "Serving", 0, ItemType.DISH),
        ("Marinara Pizza", "Serving", 0, ItemType.DISH),
    ]

    items: dict[str, Item] = {}
    for name, unit, shelf_life, item_type in definitions:
        item = Item(
            name=name,
            unit=unit,
            shelf_life_days=shelf_life,
            type=item_type,
        )
        session.add(item)
        items[name] = item

    await session.flush()  # populate PKs
    _log(f"Created {len(items)} item definitions.")
    return items


# ── Step 3: The Recipe Book (Composition) -----------------------------------

async def create_recipes(
    session: AsyncSession,
    items: dict[str, Item],
) -> None:
    """Define how prepped items and dishes are composed from inputs."""

    compositions = [
        # Pizza Dough = 0.2 Kg Flour
        (items["Pizza Dough"], items["00 Flour"], 0.2),
        # Pizza Sauce = 1 Can Tomatoes
        (items["Pizza Sauce"], items["San Marzano Tomatoes"], 1.0),
        # Margherita Pizza = 1 Dough + 0.1 L Sauce + 0.1 Kg Cheese + 1 Basil
        (items["Margherita Pizza"], items["Pizza Dough"], 1.0),
        (items["Margherita Pizza"], items["Pizza Sauce"], 0.1),
        (items["Margherita Pizza"], items["Mozzarella Cheese"], 0.1),
        (items["Margherita Pizza"], items["Fresh Basil"], 1.0),
    ]

    for output_item, input_item, qty in compositions:
        session.add(
            ItemComposition(
                output_item_id=output_item.item_id,
                input_item_id=input_item.item_id,
                quantity_required=qty,
            )
        )

    await session.flush()
    _log(f"Created {len(compositions)} recipe compositions.")


# ── Step 4: History Generation (The Time Machine) ---------------------------

async def create_initial_invoices(
    session: AsyncSession,
    items: dict[str, Item],
    base_date: datetime,
) -> dict[str, list[ItemsInventory]]:
    """Create invoices and inventory batches dated 30 days ago."""

    # Price per unit for each raw ingredient
    prices = {
        "00 Flour": 1.50,
        "San Marzano Tomatoes": 2.80,
        "Mozzarella Cheese": 8.00,
        "Fresh Basil": 1.20,
    }

    # Quantities purchased (enough for ~30 days of production)
    quantities = {
        "00 Flour": 300.0,       # Kg
        "San Marzano Tomatoes": 500.0,  # Cans
        "Mozzarella Cheese": 150.0,     # Kg
        "Fresh Basil": 1200.0,   # Bunches
    }

    invoice = Invoice(
        supplier_name="Napoli Fresh Imports",
        total_cost=sum(prices[k] * quantities[k] for k in prices),
        invoice_date=base_date,
    )
    session.add(invoice)
    await session.flush()

    batches: dict[str, list[ItemsInventory]] = {}
    for name in prices:
        item = items[name]
        exp_date = base_date + timedelta(days=item.shelf_life_days)
        batch = ItemsInventory(
            item_id=item.item_id,
            quantity_initial=quantities[name],
            quantity_current=quantities[name],
            unit_cost=prices[name],
            expiration_date=exp_date,
            source_invoice_id=invoice.invoice_id,
            created_at=base_date,
        )
        session.add(batch)
        batches[name] = [batch]

    await session.flush()
    _log(
        f"Created initial invoice #{invoice.invoice_id} "
        f"(${invoice.total_cost:,.2f}) with {len(prices)} batches."
    )
    return batches


async def simulate_daily_production(
    session: AsyncSession,
    items: dict[str, Item],
    batches: dict[str, list[ItemsInventory]],
    day_offset: int,
) -> None:
    """Simulate one day of Margherita Pizza production.

    For each pizza we:
      1. Deduct raw ingredients from the oldest batch (FIFO).
      2. Create intermediate prepped-item batches (dough, sauce).
      3. Create the dish batch and immediately deplete it (simulate sale).
    """

    now = datetime.now()
    day_date = now + timedelta(days=day_offset)
    pizza_count = _daily_pizza_count(day_offset)

    # Per-pizza ingredient requirements (mirrors recipe compositions)
    flour_per_pizza = 0.2   # Kg  (for 1 dough ball)
    tomato_per_pizza = 0.1  # Can (sauce for 1 pizza → 0.1 L, from 1 can batch)
    cheese_per_pizza = 0.1  # Kg
    basil_per_pizza = 1.0   # Bunch

    total_flour = flour_per_pizza * pizza_count
    total_tomato = tomato_per_pizza * pizza_count
    total_cheese = cheese_per_pizza * pizza_count
    total_basil = basil_per_pizza * pizza_count

    requirements = {
        "00 Flour": total_flour,
        "San Marzano Tomatoes": total_tomato,
        "Mozzarella Cheese": total_cheese,
        "Fresh Basil": total_basil,
    }

    # --- Deduct from raw-ingredient batches (FIFO) ---
    for ingredient_name, qty_needed in requirements.items():
        remaining = qty_needed
        for batch in batches.get(ingredient_name, []):
            if remaining <= 0:
                break
            deduct = min(batch.quantity_current, remaining)
            batch.quantity_current -= deduct
            remaining -= deduct
        # If remaining > 0 the stock ran out – acceptable for demo data.

    # --- Create prepped-item batches ---
    dough_batch = ItemsInventory(
        item_id=items["Pizza Dough"].item_id,
        quantity_initial=float(pizza_count),
        quantity_current=0.0,  # fully consumed immediately
        unit_cost=batches["00 Flour"][0].unit_cost * flour_per_pizza,
        expiration_date=day_date + timedelta(days=3),
        created_at=day_date,
    )
    sauce_batch = ItemsInventory(
        item_id=items["Pizza Sauce"].item_id,
        quantity_initial=pizza_count * 0.1,
        quantity_current=0.0,
        unit_cost=batches["San Marzano Tomatoes"][0].unit_cost * tomato_per_pizza,
        expiration_date=day_date + timedelta(days=5),
        created_at=day_date,
    )
    session.add_all([dough_batch, sauce_batch])
    await session.flush()

    # --- Create the dish batch (Margherita Pizza) ---
    dish_batch = ItemsInventory(
        item_id=items["Margherita Pizza"].item_id,
        quantity_initial=float(pizza_count),
        quantity_current=0.0,  # all sold
        unit_cost=0.0,
        created_at=day_date,
    )
    session.add(dish_batch)
    await session.flush()

    # --- Production logs: link input → output ---
    # We record one log entry per ingredient type for this day's batch.
    flour_batch = batches["00 Flour"][0]
    tomato_batch = batches["San Marzano Tomatoes"][0]
    cheese_batch = batches["Mozzarella Cheese"][0]
    basil_batch = batches["Fresh Basil"][0]

    production_records = [
        ProductionLog(
            output_batch_id=dough_batch.batch_id,
            input_batch_id=flour_batch.batch_id,
            quantity_used=total_flour,
            created_at=day_date,
        ),
        ProductionLog(
            output_batch_id=sauce_batch.batch_id,
            input_batch_id=tomato_batch.batch_id,
            quantity_used=total_tomato,
            created_at=day_date,
        ),
        ProductionLog(
            output_batch_id=dish_batch.batch_id,
            input_batch_id=dough_batch.batch_id,
            quantity_used=float(pizza_count),
            created_at=day_date,
        ),
        ProductionLog(
            output_batch_id=dish_batch.batch_id,
            input_batch_id=sauce_batch.batch_id,
            quantity_used=pizza_count * 0.1,
            created_at=day_date,
        ),
        ProductionLog(
            output_batch_id=dish_batch.batch_id,
            input_batch_id=cheese_batch.batch_id,
            quantity_used=total_cheese,
            created_at=day_date,
        ),
        ProductionLog(
            output_batch_id=dish_batch.batch_id,
            input_batch_id=basil_batch.batch_id,
            quantity_used=total_basil,
            created_at=day_date,
        ),
    ]
    session.add_all(production_records)
    await session.flush()


async def generate_history(
    session: AsyncSession,
    items: dict[str, Item],
) -> dict[str, list[ItemsInventory]]:
    """Create 30 days of invoices + daily production."""

    now = datetime.now()
    base_date = now - timedelta(days=30)

    # Initial purchase 30 days ago
    batches = await create_initial_invoices(session, items, base_date)

    # Daily production loop: day -29 to day -1
    for offset in range(-29, 0):
        await simulate_daily_production(session, items, batches, offset)

    _log("Generated 29 days of production history.")
    return batches


# ── Step 5: Current State (Edge Cases) --------------------------------------

async def create_edge_cases(
    session: AsyncSession,
    items: dict[str, Item],
    batches: dict[str, list[ItemsInventory]],
) -> None:
    """Create edge-case data to test UI alerts."""

    now = datetime.now()

    # 1. Low Stock – Fresh Basil at 0.5 bunches
    basil_batch = batches["Fresh Basil"][0]
    basil_batch.quantity_current = 0.5
    _log("Set Fresh Basil stock to 0.5 Bunches (Low Stock alert).")

    # 2. Expiring – Mozzarella batch expiring tomorrow
    expiring_batch = ItemsInventory(
        item_id=items["Mozzarella Cheese"].item_id,
        quantity_initial=2.0,
        quantity_current=2.0,
        unit_cost=8.00,
        expiration_date=now + timedelta(days=1),
        created_at=now - timedelta(days=12),
    )
    session.add(expiring_batch)
    await session.flush()
    _log("Created Mozzarella batch expiring tomorrow (Expiry warning).")

    # 3. Waste – 5 Kg of Flour dropped yesterday
    flour_batch = batches["00 Flour"][0]
    waste = WasteLog(
        batch_id=flour_batch.batch_id,
        quantity=5.0,
        reason=WasteReason.DROPPED,
        cost_loss=5.0 * flour_batch.unit_cost,
        created_at=now - timedelta(days=1),
    )
    session.add(waste)
    flour_batch.quantity_current = max(flour_batch.quantity_current - 5.0, 0.0)
    _log("Logged 5 Kg Flour waste (Dropped) yesterday.")

    # 4. Pending Invoice – draft invoice not yet approved
    pending_invoice = Invoice(
        supplier_name="Amalfi Coast Dairy Co.",
        total_cost=0.0,
        invoice_date=None,  # no date → draft / pending
        created_at=now,
    )
    session.add(pending_invoice)
    await session.flush()
    _log(f"Created pending invoice #{pending_invoice.invoice_id} (draft).")


# ── Main Entrypoint --------------------------------------------------------

async def main() -> None:
    _log("Starting YABA Italian Bistro seed…")

    # Step 1
    await wipe_database()

    async with async_session() as session:
        async with session.begin():
            # Step 2
            items = await create_items(session)

            # Step 3
            await create_recipes(session, items)

            # Step 4
            batches = await generate_history(session, items)

            # Step 5
            await create_edge_cases(session, items, batches)

    _log("Seeding complete! The Italian Bistro is ready. 🍕")


if __name__ == "__main__":
    asyncio.run(main())
