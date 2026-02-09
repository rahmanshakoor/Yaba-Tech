"""Inventory ingestion router for invoice uploads and OCR processing."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Invoice, Item, ItemType, ItemsInventory
from src.schemas import InvoiceUploadResponse
from src.services.ocr_service import OCRServiceInterface, get_ocr_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


async def upload_to_s3(file: UploadFile) -> str:
    """Upload a file to AWS S3 and return the URI.

    In production, this would use boto3. Currently returns a mock URI.
    """
    # Mock S3 upload - in production:
    # import boto3
    # s3 = boto3.client('s3')
    # s3.upload_fileobj(file.file, bucket, key)
    filename = file.filename or "invoice.jpg"
    return f"s3://yaba-invoices/{filename}"


@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    ocr: OCRServiceInterface = Depends(get_ocr_service),
):
    """Upload an invoice image, process with OCR, and create inventory records."""
    try:
        # 1. Upload image to S3
        image_url = await upload_to_s3(file)

        # 2. Send URI to OCR service
        ocr_result = await ocr.process_document(image_url)

        # 3. Create Invoice record
        invoice = Invoice(
            supplier_name=ocr_result.supplier_name,
            total_cost=ocr_result.total_cost,
            image_url=image_url,
        )
        db.add(invoice)
        await db.flush()

        # 4. Parse line items and create/find Items + Inventory batches
        items_added: list[dict] = []
        for line_item in ocr_result.line_items:
            # Find or create Item
            result = await db.execute(
                select(Item).where(Item.name == line_item["name"])
            )
            item = result.scalar_one_or_none()

            if not item:
                item = Item(
                    name=line_item["name"],
                    unit=line_item.get("unit", "kg"),
                    shelf_life_days=line_item.get("shelf_life_days", 30),
                    type=ItemType.RAW,
                )
                db.add(item)
                await db.flush()

            # Create inventory batch
            expiration = None
            if item.shelf_life_days > 0:
                expiration = datetime.now(timezone.utc) + timedelta(
                    days=item.shelf_life_days
                )

            batch = ItemsInventory(
                item_id=item.item_id,
                quantity_current=line_item["quantity"],
                quantity_initial=line_item["quantity"],
                expiration_date=expiration,
                source_invoice_id=invoice.invoice_id,
            )
            db.add(batch)

            items_added.append(
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "quantity": line_item["quantity"],
                    "unit": item.unit,
                }
            )

        await db.commit()

        return InvoiceUploadResponse(
            invoice_id=invoice.invoice_id,
            supplier_name=invoice.supplier_name,
            total_cost=invoice.total_cost,
            image_url=invoice.image_url,
            items_added=items_added,
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
