
import asyncio
from sqlalchemy import select
from src.database import async_session_factory
from src.models import ItemComposition, Item

async def main():
    async with async_session_factory() as db:
        result = await db.execute(
            select(ItemComposition.output_item_id)
            .limit(1)
        )
        item_id = result.scalar_one_or_none()
        if item_id:
            print(f"Found item with ingredients: {item_id}")
            # Get ingredient name
            result = await db.execute(
                select(ItemComposition).options(select(Item).where(Item.item_id == ItemComposition.input_item_id)).where(ItemComposition.output_item_id == item_id)
            )
            # Actually just printing the ID is enough to test with curl
        else:
            print("No items with ingredients found.")

if __name__ == "__main__":
    asyncio.run(main())
