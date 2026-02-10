
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database import get_db
from src.main import app
from src.models import Base, Item, ItemType, ItemsInventory, ItemComposition

@pytest.mark.asyncio
async def test_manual_production_flow():
    """Test manual batch selection and max production error."""
    # Setup in-memory DB
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Dependency override
    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        # Seed Data
        async with test_session_factory() as session:
            # 1. Setup: Create items (Raw Ingredient, Output Dish)
            ingredient = Item(name="Flour", unit="kg", type=ItemType.RAW, shelf_life_days=100)
            dish = Item(name="Bread", unit="loaf", type=ItemType.DISH, shelf_life_days=3)
            session.add_all([ingredient, dish])
            await session.flush()

            # 2. Setup: Create 2 batches for Ingredient
            batch1 = ItemsInventory(item_id=ingredient.item_id, quantity_current=10.0, quantity_initial=10.0)
            batch2 = ItemsInventory(item_id=ingredient.item_id, quantity_current=20.0, quantity_initial=20.0)
            session.add_all([batch1, batch2])
            await session.flush()
            
            # 3. Setup: Define Recipe (1 Bread needs 2kg Flour)
            composition = ItemComposition(
                output_item_id=dish.item_id,
                input_item_id=ingredient.item_id,
                quantity_required=2.0
            )
            session.add(composition)
            await session.commit()
            
            ingredient_id = ingredient.item_id
            dish_id = dish.item_id
            batch1_id = batch1.batch_id
            batch2_id = batch2.batch_id

        # Run Test via API
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            
            # 4. Test: Manual Production using Batch 2 (newer/bigger)
            # Normally FIFO would pick Batch 1 (if created first, but here created same time, usually by ID).
            # We force Batch 2.
            payload = {
                "output_item_id": dish_id,
                "quantity_to_produce": 1,
                "manual_batches": {
                    str(ingredient_id): batch2_id
                }
            }
            
            response = await client.post("/production/record", json=payload)
            assert response.status_code == 200, response.text
            data = response.json()
            assert data["quantity_produced"] == 1.0

            # Verify Batch 2 was deducted in DB
            async with test_session_factory() as session:
                from sqlalchemy import select
                result = await session.execute(select(ItemsInventory).where(ItemsInventory.batch_id == batch2_id))
                b2 = result.scalar_one()
                assert b2.quantity_current == 18.0 # 20 - 2
                
                result = await session.execute(select(ItemsInventory).where(ItemsInventory.batch_id == batch1_id))
                b1 = result.scalar_one()
                assert b1.quantity_current == 10.0

            # 5. Test: Manual Production with insufficient stock in specific batch
            # Try to use Batch 1 for 6 loaves -> needs 12kg. Batch 1 has 10kg.
            # Max possible = 10 / 2 = 5 loaves.
            payload_fail = {
                "output_item_id": dish_id,
                "quantity_to_produce": 6,
                "manual_batches": {
                    str(ingredient_id): batch1_id
                }
            }
            response_fail = await client.post("/production/record", json=payload_fail)
            assert response_fail.status_code == 400
            assert "insufficient quantity" in response_fail.text.lower()
            assert "max possible to produce: 5" in response_fail.text.lower()

    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()
