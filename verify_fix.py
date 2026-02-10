import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import app and models
from src.main import app
from src.models import Item, ItemsInventory

# Set up DB connection for verification
DATABASE_URL = "sqlite+aiosqlite:///./yaba.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

client = TestClient(app)

async def verify_db_state():
    print("\n--- Verifying Database State ---")
    async with AsyncSessionLocal() as db:
        # 1. Check Item 'Flour'
        result = await db.execute(select(Item).where(Item.name == "Flour"))
        item = result.scalar_one_or_none()
        
        if item:
            print(f"Item: {item.name}, ID: {item.item_id}")
            print(f"  Current Average Cost: {item.average_cost}")
        else:
            print("Item 'Flour' not found.")
            return

        # 2. Check latest batch
        result = await db.execute(
            select(ItemsInventory)
            .where(ItemsInventory.item_id == item.item_id)
            .order_by(ItemsInventory.created_at.desc())
            .limit(1)
        )
        batch = result.scalar_one_or_none()
        if batch:
            print(f"Latest Batch ID: {batch.batch_id}")
            print(f"  Unit Cost: {batch.unit_cost}")
            print(f"  Quantity: {batch.quantity_current}")
        else:
            print("No batches found for Flour.")

def run_test():
    print("--- Starting Upload Test ---")
    
    # Upload dummy invoice
    # The MockOCRService is hardcoded to return:
    # Flour: 10kg @ 10.0 unit_cost
    # Sugar: 5kg @ 10.0 unit_cost
    files = {'file': ('test.jpg', b'dummy', 'image/jpeg')}
    
    try:
        response = client.post("/invoices/upload", files=files)
        if response.status_code == 200:
            print("Upload Successful!")
            print(response.json())
        else:
            print(f"Upload Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception during upload: {e}")

    # Check DB state
    asyncio.run(verify_db_state())

if __name__ == "__main__":
    run_test()
