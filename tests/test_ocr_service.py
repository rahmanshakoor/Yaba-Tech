"""Tests for the OCR service interface and mock implementation."""

import pytest

from src.services.ocr_service import (
    GoogleDocumentAIOCRService,
    MockOCRService,
    OCRResult,
    get_ocr_service,
)


@pytest.mark.asyncio
async def test_mock_ocr_default():
    """Test MockOCRService with default result."""
    service = MockOCRService()
    result = await service.process_document("s3://test/doc.pdf")

    assert result.supplier_name == "Test Supplier"
    assert result.total_cost == 150.00
    assert len(result.line_items) == 2
    assert result.line_items[0]["name"] == "Flour"


@pytest.mark.asyncio
async def test_mock_ocr_custom_result():
    """Test MockOCRService with custom result."""
    custom = OCRResult(
        supplier_name="Custom Supplier",
        total_cost=500.0,
        line_items=[{"name": "Beef", "quantity": 50.0, "unit": "kg"}],
    )
    service = MockOCRService(mock_result=custom)
    result = await service.process_document("s3://bucket/invoice.jpg")

    assert result.supplier_name == "Custom Supplier"
    assert result.total_cost == 500.0
    assert len(result.line_items) == 1


@pytest.mark.asyncio
async def test_google_doc_ai_mock():
    """Test GoogleDocumentAIOCRService returns mock response."""
    service = GoogleDocumentAIOCRService(
        project_id="test", location="us", processor_id="proc123"
    )
    result = await service.process_document("gs://bucket/doc.pdf")

    assert result.supplier_name == "Mock Supplier"
    assert result.total_cost == 0.0
    assert len(result.line_items) == 0


@pytest.mark.asyncio
async def test_ocr_result_attributes():
    """Test OCRResult data class."""
    result = OCRResult(
        supplier_name="Farm Fresh",
        total_cost=200.0,
        line_items=[
            {"name": "Lettuce", "quantity": 10.0, "unit": "kg"},
            {"name": "Tomatoes", "quantity": 5.0, "unit": "kg"},
        ],
    )
    assert result.supplier_name == "Farm Fresh"
    assert result.total_cost == 200.0
    assert len(result.line_items) == 2


def test_get_ocr_service_returns_instance():
    """Test that get_ocr_service returns a valid service."""
    service = get_ocr_service()
    assert service is not None
