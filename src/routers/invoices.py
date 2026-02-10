"""Manual Invoices router for creating and managing invoices."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models import Invoice, Item, ItemsInventory, ProductionLog
from src.schemas import InvoiceResponse, ManualInvoiceCreate
from src.services.cost_service import calculate_moving_average

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    db: AsyncSession = Depends(get_db),
):
    """List past invoices (summary view)."""
    result = await db.execute(
        select(Invoice).order_by(Invoice.created_at.desc())
    )
    return result.scalars().all()


@router.post("/manual", response_model=InvoiceResponse, status_code=201)
async def create_manual_invoice(
    invoice_in: ManualInvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a manual invoice and automatically create inventory batches."""
    try:
        invoice_date = None
        if invoice_in.date:
            invoice_date = datetime.fromisoformat(invoice_in.date)

        invoice = Invoice(
            supplier_name=invoice_in.supplier_name,
            total_cost=invoice_in.total_cost,
            invoice_date=invoice_date,
        )
        db.add(invoice)
        await db.flush()

        for line_item in invoice_in.items:
            # Verify item exists
            result = await db.execute(
                select(Item).where(Item.item_id == line_item.item_id)
            )
            item = result.scalar_one_or_none()
            if not item:
                raise HTTPException(
                    status_code=404,
                    detail=f"Item with id {line_item.item_id} not found",
                )

            expiration = None
            if item.shelf_life_days > 0:
                expiration = datetime.now(timezone.utc) + timedelta(
                    days=item.shelf_life_days
                )

            # If short shipment, record only the actual quantity received
            # but keep total_cost unchanged (matches bank statement)
            actual_quantity = line_item.quantity
            if line_item.is_short_shipment:
                # In a production system, a "Supplier Credit Needed" note
                # would be persisted to a notes/flags table for follow-up.
                pass

            # Update moving average cost for raw items (before adding the batch)
            await calculate_moving_average(
                db,
                line_item.item_id,
                actual_quantity,
                line_item.unit_cost,
            )

            batch = ItemsInventory(
                item_id=line_item.item_id,
                quantity_current=actual_quantity,
                quantity_initial=actual_quantity,
                unit_cost=line_item.unit_cost,
                expiration_date=expiration,
                source_invoice_id=invoice.invoice_id,
            )
            db.add(batch)

        await db.commit()
        await db.refresh(invoice)
        return invoice

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an invoice. Reverts inventory if batches haven't been used."""
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Find all inventory batches created by this invoice
    batches_result = await db.execute(
        select(ItemsInventory).where(
            ItemsInventory.source_invoice_id == invoice_id
        )
    )
    batches = batches_result.scalars().all()

    # Check if any batch has been used in production
    for batch in batches:
        usage_result = await db.execute(
            select(ProductionLog).where(
                ProductionLog.input_batch_id == batch.batch_id
            )
        )
        if usage_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Cannot delete invoice; items already consumed",
            )

    # Remove batches and invoice
    for batch in batches:
        await db.delete(batch)

    await db.delete(invoice)
    await db.commit()
    return {"detail": "Invoice deleted", "invoice_id": invoice_id}
