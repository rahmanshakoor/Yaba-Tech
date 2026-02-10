"""Tests for invoice ingestion with mocked S3 and OCR."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database import get_db
from src.main import app
from src.models import Base, Invoice, Item, ItemsInventory
from src.services.ocr_service import MockOCRService, OCRResult, get_ocr_service


@pytest.mark.asyncio
async def test_upload_invoice_with_mock_ocr():
    """Test invoice upload endpoint with mocked S3 and OCR responses."""
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    mock_ocr = MockOCRService(
        mock_result=OCRResult(
            supplier_name="Fresh Farm Co",
            total_cost=250.00,
            line_items=[
                {"name": "Tomatoes", "quantity": 20.0, "unit": "kg"},
                {"name": "Onions", "quantity": 15.0, "unit": "kg"},
            ],
        )
    )

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    def override_get_ocr():
        return mock_ocr

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ocr_service] = override_get_ocr

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Simulate file upload
            response = await client.post(
                "/invoices/upload",
                files={"file": ("invoice.jpg", b"fake image content", "image/jpeg")},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["supplier_name"] == "Fresh Farm Co"
            assert data["total_cost"] == 250.00
            assert len(data["items_added"]) == 2
            assert data["items_added"][0]["name"] == "Tomatoes"
            assert data["items_added"][0]["quantity"] == 20.0
            assert data["items_added"][1]["name"] == "Onions"

        # Verify database records
        async with test_session_factory() as session:
            invoices = (await session.execute(select(Invoice))).scalars().all()
            assert len(invoices) == 1
            assert invoices[0].supplier_name == "Fresh Farm Co"

            items = (await session.execute(select(Item))).scalars().all()
            assert len(items) == 2

            batches = (await session.execute(select(ItemsInventory))).scalars().all()
            assert len(batches) == 2
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_upload_invoice_creates_new_items():
    """Test that new items are created from OCR results when they don't exist."""
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    mock_ocr = MockOCRService(
        mock_result=OCRResult(
            supplier_name="Spice World",
            total_cost=75.00,
            line_items=[
                {"name": "Cumin", "quantity": 2.0, "unit": "kg"},
            ],
        )
    )

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    def override_get_ocr():
        return mock_ocr

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ocr_service] = override_get_ocr

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/invoices/upload",
                files={"file": ("receipt.png", b"image data", "image/png")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["items_added"][0]["name"] == "Cumin"

        # Verify the item was created as RAW type
        async with test_session_factory() as session:
            result = await session.execute(select(Item).where(Item.name == "Cumin"))
            item = result.scalar_one()
            assert item.unit == "kg"
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_mock_ocr_service():
    """Test the MockOCRService directly."""
    mock = MockOCRService(
        mock_result=OCRResult(
            supplier_name="Test",
            total_cost=100.0,
            line_items=[{"name": "Salt", "quantity": 1.0, "unit": "kg"}],
        )
    )
    result = await mock.process_document("s3://test/invoice.jpg")
    assert result.supplier_name == "Test"
    assert result.total_cost == 100.0
    assert len(result.line_items) == 1
    assert result.line_items[0]["name"] == "Salt"
