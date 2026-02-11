
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.database import get_db
from src.models import Item, ItemType, Invoice, ItemsInventory

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
        name="Test Flour",
        unit="kg",
        shelf_life_days=30,
        type=ItemType.RAW,
        average_cost=0.0
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item

@pytest.mark.asyncio
async def test_create_manual_invoice_creates_batches(
    client: AsyncClient, db_session: AsyncSession, raw_item: Item
):
    """Test that creating a manual invoice creates corresponding inventory batches."""
    payload = {
        "supplier_name": "Test Supplier",
        "date": "2023-10-27T10:00:00",
        "total_cost": 100.0,
        "items": [
            {
                "item_id": raw_item.item_id,
                "quantity": 10.0,
                "unit_cost": 10.0,
                "is_short_shipment": False
            }
        ]
    }

    response = await client.post("/invoices/manual", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["supplier_name"] == "Test Supplier"

    # Verify batch created
    invoice_id = data["invoice_id"]
    result = await db_session.execute(
        select(ItemsInventory).where(ItemsInventory.source_invoice_id == invoice_id)
    )
    batches = result.scalars().all()
    assert len(batches) == 1
    assert batches[0].item_id == raw_item.item_id
    assert batches[0].quantity_initial == 10.0
    assert batches[0].unit_cost == 10.0

@pytest.mark.asyncio
async def test_list_invoices_includes_batches(
    client: AsyncClient, db_session: AsyncSession, raw_item: Item
):
    """Test that listing invoices includes the batch details."""
    # Create an invoice first
    invoice = Invoice(
        supplier_name="List Supplier",
        total_cost=50.0,
        invoice_date=None
    )
    db_session.add(invoice)
    await db_session.flush()

    batch = ItemsInventory(
        item_id=raw_item.item_id,
        quantity_current=5.0,
        quantity_initial=5.0,
        unit_cost=10.0,
        source_invoice_id=invoice.invoice_id
    )
    db_session.add(batch)
    await db_session.commit()

    response = await client.get("/invoices/")
    assert response.status_code == 200
    data = response.json()
    
    # Find our invoice
    target_invoice = next((inv for inv in data if inv["invoice_id"] == invoice.invoice_id), None)
    assert target_invoice is not None
    assert "batches" in target_invoice
    assert len(target_invoice["batches"]) == 1
    batch_data = target_invoice["batches"][0]
    assert batch_data["item_name"] == raw_item.name
    assert batch_data["quantity_initial"] == 5.0
    assert batch_data["unit_cost"] == 10.0
