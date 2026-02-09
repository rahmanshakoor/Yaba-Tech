"""Tests for UI flow user stories: recipe editing, manual invoices,
stock corrections, and invoice deletion guard."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database import get_db
from src.main import app
from src.models import Base, Item, ItemComposition, ItemsInventory, ItemType, ProductionLog


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _create_test_env():
    """Create a fresh test database and return engine + session factory."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, session_factory


@pytest.mark.asyncio
async def test_recipe_editing():
    """Create a 'Burger', add 'Bun' and 'Patty' as ingredients,
    then change the quantity of 'Patty'."""
    engine, session_factory = await _create_test_env()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Create items: Burger (Dish), Bun (Raw), Patty (Raw)
            burger_resp = await client.post(
                "/items/",
                json={"name": "Burger", "unit": "piece", "shelf_life_days": 1, "type": "Dish"},
            )
            assert burger_resp.status_code == 201
            burger_id = burger_resp.json()["item_id"]

            bun_resp = await client.post(
                "/items/",
                json={"name": "Bun", "unit": "piece", "shelf_life_days": 5, "type": "Raw"},
            )
            assert bun_resp.status_code == 201
            bun_id = bun_resp.json()["item_id"]

            patty_resp = await client.post(
                "/items/",
                json={"name": "Patty", "unit": "piece", "shelf_life_days": 3, "type": "Raw"},
            )
            assert patty_resp.status_code == 201
            patty_id = patty_resp.json()["item_id"]

            # Add Bun as ingredient (1 bun per burger)
            resp = await client.post(
                f"/items/{burger_id}/recipe",
                json={"input_item_id": bun_id, "quantity_required": 1.0},
            )
            assert resp.status_code == 201

            # Add Patty as ingredient (1 patty per burger)
            resp = await client.post(
                f"/items/{burger_id}/recipe",
                json={"input_item_id": patty_id, "quantity_required": 1.0},
            )
            assert resp.status_code == 201

            # Verify recipe
            recipe_resp = await client.get(f"/items/{burger_id}/recipe")
            assert recipe_resp.status_code == 200
            recipe = recipe_resp.json()
            assert len(recipe["ingredients"]) == 2

            # Change quantity of Patty to 2
            resp = await client.post(
                f"/items/{burger_id}/recipe",
                json={"input_item_id": patty_id, "quantity_required": 2.0},
            )
            assert resp.status_code == 201
            assert resp.json()["detail"] == "Recipe ingredient updated"

            # Verify updated recipe
            recipe_resp = await client.get(f"/items/{burger_id}/recipe")
            assert recipe_resp.status_code == 200
            recipe = recipe_resp.json()
            patty_ingredient = [
                i for i in recipe["ingredients"] if i["input_item_id"] == patty_id
            ][0]
            assert patty_ingredient["quantity_required"] == 2.0
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_manual_invoice():
    """Submit a JSON invoice and verify that ItemsInventory count increases."""
    engine, session_factory = await _create_test_env()

    # Seed an item
    async with session_factory() as session:
        tomato = Item(
            name="Tomatoes", unit="kg", shelf_life_days=7, type=ItemType.RAW
        )
        session.add(tomato)
        await session.commit()
        tomato_id = tomato.item_id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Check initial inventory summary
            summary_resp = await client.get("/inventory/summary")
            assert summary_resp.status_code == 200
            initial_items = summary_resp.json()["items"]
            initial_tomato = [
                i for i in initial_items if i["item_id"] == tomato_id
            ]
            initial_stock = initial_tomato[0]["total_stock"] if initial_tomato else 0

            # Submit manual invoice
            invoice_resp = await client.post(
                "/invoices/manual",
                json={
                    "supplier_name": "Fresh Farms",
                    "date": "2025-01-15",
                    "total_cost": 50.0,
                    "items": [
                        {"item_id": tomato_id, "quantity": 10.0, "unit_cost": 5.0}
                    ],
                },
            )
            assert invoice_resp.status_code == 201

            # Verify inventory increased
            summary_resp = await client.get("/inventory/summary")
            assert summary_resp.status_code == 200
            updated_items = summary_resp.json()["items"]
            updated_tomato = [
                i for i in updated_items if i["item_id"] == tomato_id
            ]
            assert len(updated_tomato) == 1
            assert updated_tomato[0]["total_stock"] == initial_stock + 10.0

            # Also verify invoice appears in list
            invoices_resp = await client.get("/invoices/")
            assert invoices_resp.status_code == 200
            invoices = invoices_resp.json()
            assert len(invoices) >= 1
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_stock_correction():
    """Manually change a batch quantity from 10 to 5 and verify
    the inventory summary reflects the new total."""
    engine, session_factory = await _create_test_env()

    # Seed item + batch
    async with session_factory() as session:
        flour = Item(
            name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW
        )
        session.add(flour)
        await session.flush()

        batch = ItemsInventory(
            item_id=flour.item_id,
            quantity_current=10.0,
            quantity_initial=10.0,
        )
        session.add(batch)
        await session.commit()
        flour_id = flour.item_id
        batch_id = batch.batch_id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Verify initial stock is 10
            summary_resp = await client.get("/inventory/summary")
            assert summary_resp.status_code == 200
            flour_item = [
                i for i in summary_resp.json()["items"]
                if i["item_id"] == flour_id
            ]
            assert flour_item[0]["total_stock"] == 10.0

            # Correct batch to 5
            update_resp = await client.put(
                f"/inventory/batch/{batch_id}",
                json={"quantity_current": 5.0},
            )
            assert update_resp.status_code == 200
            assert update_resp.json()["quantity_current"] == 5.0

            # Verify summary reflects new total
            summary_resp = await client.get("/inventory/summary")
            assert summary_resp.status_code == 200
            flour_item = [
                i for i in summary_resp.json()["items"]
                if i["item_id"] == flour_id
            ]
            assert flour_item[0]["total_stock"] == 5.0
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_invoice_deletion_guard():
    """Create an invoice -> Consume an item from it in production ->
    Try to delete the invoice -> Expect 400 Error."""
    engine, session_factory = await _create_test_env()

    # Seed: a raw item (Flour), a dish (Cake) with recipe, and stock
    async with session_factory() as session:
        flour = Item(
            name="Flour", unit="kg", shelf_life_days=180, type=ItemType.RAW
        )
        cake = Item(
            name="Cake", unit="piece", shelf_life_days=3, type=ItemType.DISH
        )
        session.add_all([flour, cake])
        await session.flush()

        comp = ItemComposition(
            output_item_id=cake.item_id,
            input_item_id=flour.item_id,
            quantity_required=0.5,
        )
        session.add(comp)
        await session.commit()
        flour_id = flour.item_id
        cake_id = cake.item_id

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            # Create manual invoice adding flour
            invoice_resp = await client.post(
                "/invoices/manual",
                json={
                    "supplier_name": "Mill Co",
                    "total_cost": 20.0,
                    "items": [
                        {"item_id": flour_id, "quantity": 10.0, "unit_cost": 2.0}
                    ],
                },
            )
            assert invoice_resp.status_code == 201
            invoice_id = invoice_resp.json()["invoice_id"]

            # Produce a cake (consumes flour from the invoice batch)
            prod_resp = await client.post(
                "/inventory/production/manual",
                json={"output_item_id": cake_id, "quantity_to_produce": 1.0},
            )
            assert prod_resp.status_code == 200

            # Try to delete the invoice -> expect 400
            del_resp = await client.delete(f"/invoices/{invoice_id}")
            assert del_resp.status_code == 400
            assert "items already consumed" in del_resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
