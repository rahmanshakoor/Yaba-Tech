
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.database import get_db
from src.models import Item, ItemType, ItemsInventory

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
async def raw_item(db_session: AsyncSession):
    item = Item(
        name="Test Sugar",
        unit="kg",
        shelf_life_days=300,
        type=ItemType.RAW,
        average_cost=1.5
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item

@pytest.mark.asyncio
async def test_deplete_stock_success(client: AsyncClient, db_session: AsyncSession, raw_item: Item):
    """Test successful stock depletion with multiple batches (FIFO)."""
    # Create two batches
    batch1 = ItemsInventory(
        item_id=raw_item.item_id,
        quantity_current=10.0,
        quantity_initial=10.0,
        unit_cost=1.5
    )
    batch2 = ItemsInventory(
        item_id=raw_item.item_id,
        quantity_current=5.0,
        quantity_initial=5.0,
        unit_cost=1.5
    )
    db_session.add_all([batch1, batch2])
    await db_session.commit()

    # Deplete 12 units (should take 10 from batch1, 2 from batch2)
    response = await client.post("/inventory/deplete", json={
        "item_id": raw_item.item_id,
        "quantity": 12.0
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == raw_item.item_id
    assert data["total_depleted"] == 12.0
    assert len(data["batches_affected"]) == 2
    
    # Check DB state
    await db_session.refresh(batch1)
    await db_session.refresh(batch2)
    assert batch1.quantity_current == 0.0
    assert batch2.quantity_current == 3.0

@pytest.mark.asyncio
async def test_deplete_insufficient_stock(client: AsyncClient, db_session: AsyncSession, raw_item: Item):
    """Test error when trying to deplete more than available."""
    batch = ItemsInventory(
        item_id=raw_item.item_id,
        quantity_current=5.0,
        quantity_initial=5.0,
        unit_cost=1.5
    )
    db_session.add(batch)
    await db_session.commit()

    response = await client.post("/inventory/deplete", json={
        "item_id": raw_item.item_id,
        "quantity": 10.0
    })
    
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]

@pytest.mark.asyncio
async def test_deplete_invalid_quantity(client: AsyncClient, raw_item: Item):
    """Test error when quantity is zero or negative."""
    response = await client.post("/inventory/deplete", json={
        "item_id": raw_item.item_id,
        "quantity": 0.0
    })
    assert response.status_code == 400
    
    response = await client.post("/inventory/deplete", json={
        "item_id": raw_item.item_id,
        "quantity": -5.0
    })
    assert response.status_code == 400
