"""Definitions router for managing Item master data and Recipes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models import Item, ItemComposition, ItemType
from src.schemas import (
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    RecipeIngredient,
    RecipeIngredientResponse,
    RecipeResponse,
)

router = APIRouter(prefix="/items", tags=["definitions"])


@router.get("/", response_model=list[ItemResponse])
async def list_items(
    type: Optional[ItemType] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """List items with optional type filter (Raw/Prepped/Dish)."""
    query = select(Item).where(Item.is_archived == False)  # noqa: E712
    if type is not None:
        query = query.where(Item.type == type)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new Item definition."""
    existing = await db.execute(select(Item).where(Item.name == item_in.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Item name already exists")

    item = Item(
        name=item_in.name,
        unit=item_in.unit,
        shelf_life_days=item_in.shelf_life_days,
        type=item_in.type,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_in: ItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Edit item details (Name, Unit, Shelf Life)."""
    result = await db.execute(select(Item).where(Item.item_id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_in.name is not None:
        item.name = item_in.name
    if item_in.unit is not None:
        item.unit = item_in.unit
    if item_in.shelf_life_days is not None:
        item.shelf_life_days = item_in.shelf_life_days

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=200)
async def archive_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete (archive) an item."""
    result = await db.execute(select(Item).where(Item.item_id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_archived = True
    await db.commit()
    return {"detail": "Item archived", "item_id": item_id}


@router.post("/{item_id}/recipe", status_code=201)
async def add_recipe_ingredient(
    item_id: int,
    ingredient: RecipeIngredient,
    db: AsyncSession = Depends(get_db),
):
    """Add an ingredient to a Dish/Prepped item's recipe (ItemComposition)."""
    result = await db.execute(select(Item).where(Item.item_id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.type == ItemType.RAW:
        raise HTTPException(
            status_code=400, detail="Raw items cannot have recipes"
        )

    input_result = await db.execute(
        select(Item).where(Item.item_id == ingredient.input_item_id)
    )
    if not input_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Input item not found")

    # Check if composition already exists and update it
    existing = await db.execute(
        select(ItemComposition).where(
            ItemComposition.output_item_id == item_id,
            ItemComposition.input_item_id == ingredient.input_item_id,
        )
    )
    comp = existing.scalar_one_or_none()
    if comp:
        comp.quantity_required = ingredient.quantity_required
        await db.commit()
        return {
            "detail": "Recipe ingredient updated",
            "composition_id": comp.composition_id,
        }

    comp = ItemComposition(
        output_item_id=item_id,
        input_item_id=ingredient.input_item_id,
        quantity_required=ingredient.quantity_required,
    )
    db.add(comp)
    await db.commit()
    await db.refresh(comp)
    return {
        "detail": "Recipe ingredient added",
        "composition_id": comp.composition_id,
    }


@router.get("/{item_id}/recipe", response_model=RecipeResponse)
async def get_recipe(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Fetch the full recipe tree for a specific dish."""
    result = await db.execute(select(Item).where(Item.item_id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    comp_result = await db.execute(
        select(ItemComposition)
        .where(ItemComposition.output_item_id == item_id)
        .options(selectinload(ItemComposition.input_item))
    )
    compositions = comp_result.scalars().all()

    ingredients = [
        RecipeIngredientResponse(
            composition_id=c.composition_id,
            input_item_id=c.input_item_id,
            input_item_name=c.input_item.name,
            quantity_required=c.quantity_required,
        )
        for c in compositions
    ]

    return RecipeResponse(
        output_item_id=item.item_id,
        output_item_name=item.name,
        ingredients=ingredients,
    )
