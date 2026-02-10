"""Tests for recipe_service composition logic and the composition endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database import get_db
from src.main import app
from src.models import Base, Item, ItemComposition, ItemType
from src.services.recipe_service import save_composition


@pytest.mark.asyncio
async def test_save_composition_prepped_with_raw(db_session):
    """Prepped items accept only Raw ingredients."""
    raw1 = Item(name="Tomato", unit="kg", shelf_life_days=7, type=ItemType.RAW)
    raw2 = Item(name="Onion", unit="kg", shelf_life_days=14, type=ItemType.RAW)
    prepped = Item(name="Salsa", unit="liters", shelf_life_days=3, type=ItemType.PREPPED)
    db_session.add_all([raw1, raw2, prepped])
    await db_session.flush()

    compositions = await save_composition(
        db_session,
        prepped.item_id,
        [
            {"input_item_id": raw1.item_id, "quantity": 2.0},
            {"input_item_id": raw2.item_id, "quantity": 1.0},
        ],
    )

    assert len(compositions) == 2
    assert compositions[0].output_item_id == prepped.item_id
    assert compositions[0].quantity_required == 2.0


@pytest.mark.asyncio
async def test_save_composition_prepped_rejects_prepped_input(db_session):
    """Prepped items cannot use Prepped ingredients."""
    raw = Item(name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW)
    prepped_input = Item(name="Dough", unit="kg", shelf_life_days=1, type=ItemType.PREPPED)
    prepped_target = Item(name="Pasta", unit="kg", shelf_life_days=2, type=ItemType.PREPPED)
    db_session.add_all([raw, prepped_input, prepped_target])
    await db_session.flush()

    with pytest.raises(ValueError, match="Prepped items can only use Raw ingredients"):
        await save_composition(
            db_session,
            prepped_target.item_id,
            [{"input_item_id": prepped_input.item_id, "quantity": 1.0}],
        )


@pytest.mark.asyncio
async def test_save_composition_dish_with_raw_and_prepped(db_session):
    """Dish items accept both Raw and Prepped ingredients."""
    raw = Item(name="Cheese", unit="kg", shelf_life_days=30, type=ItemType.RAW)
    prepped = Item(name="Tomato Sauce", unit="liters", shelf_life_days=3, type=ItemType.PREPPED)
    dish = Item(name="Pizza", unit="pieces", shelf_life_days=1, type=ItemType.DISH)
    db_session.add_all([raw, prepped, dish])
    await db_session.flush()

    compositions = await save_composition(
        db_session,
        dish.item_id,
        [
            {"input_item_id": raw.item_id, "quantity": 0.3},
            {"input_item_id": prepped.item_id, "quantity": 0.2},
        ],
    )

    assert len(compositions) == 2


@pytest.mark.asyncio
async def test_save_composition_dish_rejects_dish_input(db_session):
    """Dish items cannot use other Dish items as ingredients."""
    dish_input = Item(name="Sub-Dish", unit="pieces", shelf_life_days=1, type=ItemType.DISH)
    dish_target = Item(name="Combo Platter", unit="pieces", shelf_life_days=1, type=ItemType.DISH)
    db_session.add_all([dish_input, dish_target])
    await db_session.flush()

    with pytest.raises(ValueError, match="Dish items can only use Raw or Prepped"):
        await save_composition(
            db_session,
            dish_target.item_id,
            [{"input_item_id": dish_input.item_id, "quantity": 1.0}],
        )


@pytest.mark.asyncio
async def test_save_composition_raw_target_rejected(db_session):
    """Raw items cannot have compositions."""
    raw = Item(name="Garlic", unit="kg", shelf_life_days=30, type=ItemType.RAW)
    raw2 = Item(name="Salt", unit="kg", shelf_life_days=365, type=ItemType.RAW)
    db_session.add_all([raw, raw2])
    await db_session.flush()

    with pytest.raises(ValueError, match="Raw items cannot have compositions"):
        await save_composition(
            db_session,
            raw.item_id,
            [{"input_item_id": raw2.item_id, "quantity": 0.5}],
        )


@pytest.mark.asyncio
async def test_save_composition_clears_existing(db_session):
    """Saving a composition replaces existing rows."""
    raw1 = Item(name="Lettuce", unit="kg", shelf_life_days=5, type=ItemType.RAW)
    raw2 = Item(name="Cucumber", unit="kg", shelf_life_days=7, type=ItemType.RAW)
    prepped = Item(name="Salad Mix", unit="kg", shelf_life_days=2, type=ItemType.PREPPED)
    db_session.add_all([raw1, raw2, prepped])
    await db_session.flush()

    # First save
    await save_composition(
        db_session,
        prepped.item_id,
        [{"input_item_id": raw1.item_id, "quantity": 1.0}],
    )
    await db_session.commit()

    # Second save replaces first
    compositions = await save_composition(
        db_session,
        prepped.item_id,
        [{"input_item_id": raw2.item_id, "quantity": 2.0}],
    )
    await db_session.commit()

    assert len(compositions) == 1
    assert compositions[0].input_item_id == raw2.item_id
    assert compositions[0].quantity_required == 2.0


@pytest.mark.asyncio
async def test_composition_api_endpoint_success():
    """Test the POST /items/{item_id}/composition endpoint."""
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Seed data
    async with test_session_factory() as session:
        raw = Item(name="Tomato", unit="kg", shelf_life_days=7, type=ItemType.RAW)
        prepped = Item(name="Salsa", unit="liters", shelf_life_days=3, type=ItemType.PREPPED)
        session.add_all([raw, prepped])
        await session.commit()
        raw_id = raw.item_id
        prepped_id = prepped.item_id

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/items/{prepped_id}/composition",
                json=[{"input_item_id": raw_id, "quantity": 2.0}],
            )
            assert response.status_code == 200
            data = response.json()
            assert data["output_item_id"] == prepped_id
            assert len(data["compositions"]) == 1
            assert data["compositions"][0]["input_item_id"] == raw_id
            assert data["compositions"][0]["quantity_required"] == 2.0
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_composition_api_endpoint_validation_error():
    """Test that invalid ingredient types return 400."""
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Seed data: Prepped target with a Prepped input (invalid)
    async with test_session_factory() as session:
        prepped_input = Item(name="Dough", unit="kg", shelf_life_days=1, type=ItemType.PREPPED)
        prepped_target = Item(name="Pasta", unit="kg", shelf_life_days=2, type=ItemType.PREPPED)
        session.add_all([prepped_input, prepped_target])
        await session.commit()
        input_id = prepped_input.item_id
        target_id = prepped_target.item_id

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/items/{target_id}/composition",
                json=[{"input_item_id": input_id, "quantity": 1.0}],
            )
            assert response.status_code == 400
            assert "Prepped items can only use Raw ingredients" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()
