"""Google Cloud Document AI OCR service interface.

This module provides the interface for OCR processing. The actual Google Cloud
Document AI integration is mocked for now but the interface is production-ready.
"""

from typing import Protocol


class OCRResult:
    """Represents parsed OCR data from an invoice."""

    def __init__(
        self,
        supplier_name: str,
        total_cost: float,
        line_items: list[dict],
    ):
        self.supplier_name = supplier_name
        self.total_cost = total_cost
        self.line_items = line_items  # [{"name": str, "quantity": float, "unit": str, "unit_cost": float}]


class OCRServiceInterface(Protocol):
    """Protocol defining the OCR service interface."""

    async def process_document(self, document_uri: str) -> OCRResult: ...


class GoogleDocumentAIOCRService:
    """Google Cloud Document AI integration for invoice OCR.

    This service sends a document URI to Google Cloud Document AI
    for processing and returns structured invoice data.
    """

    def __init__(
        self,
        project_id: str = "",
        location: str = "us",
        processor_id: str = "",
    ):
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id

    async def process_document(self, document_uri: str) -> OCRResult:
        """Process a document via Google Cloud Document AI.

        In production, this would call the Document AI API.
        Currently returns a mock response.
        """
        # Mock implementation - in production, this would use:
        # from google.cloud import documentai_v1 as documentai
        return OCRResult(
            supplier_name="Mock Supplier",
            total_cost=0.0,
            line_items=[],
        )


class MockOCRService:
    """Mock OCR service for testing and development."""

    def __init__(self, mock_result: OCRResult | None = None):
        self._mock_result = mock_result or OCRResult(
            supplier_name="Test Supplier",
            total_cost=150.00,
            line_items=[
                {"name": "Flour", "quantity": 10.0, "unit": "kg", "unit_cost": 10.0},
                {"name": "Sugar", "quantity": 5.0, "unit": "kg", "unit_cost": 10.0},
            ],
        )

    async def process_document(self, document_uri: str) -> OCRResult:
        return self._mock_result


# Default service instance (use MockOCRService for development)
ocr_service: OCRServiceInterface = MockOCRService()


def get_ocr_service() -> OCRServiceInterface:
    return ocr_service
