"""Tests for production recording with FIFO logic."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database import get_db
from src.main import app
from src.models import Base, Item, ItemComposition, ItemsInventory, ItemType
from src.services.inventory_service import produce_item


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _setup_recipe(session: AsyncSession):
    """Set up a simple recipe: Cake requires Flour(0.5kg) and Sugar(0.2kg)."""
    flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    sugar = Item(name="Sugar", unit="kg", shelf_life_days=365, type=ItemType.RAW)
    cake = Item(name="Cake", unit="kg", shelf_life_days=3, type=ItemType.DISH)

    session.add_all([flour, sugar, cake])
    await session.flush()

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
    session.add_all([comp1, comp2])
    await session.flush()

    return flour, sugar, cake


@pytest.mark.asyncio
async def test_production_fifo_logic(db_session):
    """Test that FIFO logic uses oldest batch first."""
    flour, sugar, cake = await _setup_recipe(db_session)

    # Add two flour batches (older one first)
    batch1 = ItemsInventory(
        item_id=flour.item_id,
        quantity_current=3.0,
        quantity_initial=3.0,
    )
    batch2 = ItemsInventory(
        item_id=flour.item_id,
        quantity_current=5.0,
        quantity_initial=5.0,
    )
    sugar_batch = ItemsInventory(
        item_id=sugar.item_id,
        quantity_current=10.0,
        quantity_initial=10.0,
    )
    db_session.add_all([batch1, batch2, sugar_batch])
    await db_session.flush()

    # Produce 10 cakes -> needs 5kg flour, 2kg sugar
    result = await produce_item(db_session, cake.item_id, 10.0)

    assert result["output_item_id"] == cake.item_id
    assert result["quantity_produced"] == 10.0

    # Verify FIFO: batch1 should be fully used (3.0), batch2 partially (2.0)
    await db_session.refresh(batch1)
    await db_session.refresh(batch2)
    await db_session.refresh(sugar_batch)

    assert batch1.quantity_current == 0.0  # fully consumed
    assert batch2.quantity_current == 3.0  # 5.0 - 2.0
    assert sugar_batch.quantity_current == 8.0  # 10.0 - 2.0


@pytest.mark.asyncio
async def test_production_insufficient_stock(db_session):
    """Test that insufficient stock raises ValueError."""
    flour, sugar, cake = await _setup_recipe(db_session)

    # Only add a small amount of flour
    batch = ItemsInventory(
        item_id=flour.item_id,
        quantity_current=1.0,
        quantity_initial=1.0,
    )
    sugar_batch = ItemsInventory(
        item_id=sugar.item_id,
        quantity_current=10.0,
        quantity_initial=10.0,
    )
    db_session.add_all([batch, sugar_batch])
    await db_session.flush()

    # Try to produce 10 cakes -> needs 5kg flour, but only 1kg available
    with pytest.raises(ValueError, match="Insufficient stock"):
        await produce_item(db_session, cake.item_id, 10.0)


@pytest.mark.asyncio
async def test_production_no_recipe(db_session):
    """Test that producing an item without a recipe raises ValueError."""
    item = Item(name="Mystery", unit="kg", shelf_life_days=30, type=ItemType.DISH)
    db_session.add(item)
    await db_session.flush()

    with pytest.raises(ValueError, match="No recipe found"):
        await produce_item(db_session, item.item_id, 1.0)


@pytest.mark.asyncio
async def test_production_api_endpoint():
    """Test the production API endpoint returns 400 on insufficient stock."""
    # Create a fresh test database
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Try to produce something that doesn't have a recipe
            response = await client.post(
                "/production/record",
                json={"output_item_id": 999, "quantity_to_produce": 1.0},
            )
            assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_production_api_success():
    """Test successful production via the API endpoint."""
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Seed data
    async with test_session_factory() as session:
        flour = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
        sugar = Item(name="Sugar", unit="kg", shelf_life_days=365, type=ItemType.RAW)
        cake = Item(name="Cake", unit="kg", shelf_life_days=3, type=ItemType.DISH)
        session.add_all([flour, sugar, cake])
        await session.flush()

        session.add_all([
            ItemComposition(
                output_item_id=cake.item_id,
                input_item_id=flour.item_id,
                quantity_required=0.5,
            ),
            ItemComposition(
                output_item_id=cake.item_id,
                input_item_id=sugar.item_id,
                quantity_required=0.2,
            ),
        ])
        await session.flush()

        session.add_all([
            ItemsInventory(
                item_id=flour.item_id,
                quantity_current=10.0,
                quantity_initial=10.0,
            ),
            ItemsInventory(
                item_id=sugar.item_id,
                quantity_current=10.0,
                quantity_initial=10.0,
            ),
        ])
        await session.commit()

        cake_id = cake.item_id

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/production/record",
                json={"output_item_id": cake_id, "quantity_to_produce": 2.0},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["output_item_id"] == cake_id
            assert data["quantity_produced"] == 2.0
            assert len(data["ingredients_used"]) > 0
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()
