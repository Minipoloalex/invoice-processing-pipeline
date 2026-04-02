import httpx
import logging
from models import ERPVendor
from config import ERP_API_KEY, ERP_BASE_URL
from typing import Optional

logger = logging.getLogger(__name__)

_HEADERS = {"X-ERP-API-Key": ERP_API_KEY}


async def fetch_companies() -> list[ERPVendor]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{ERP_BASE_URL}/companies", headers=_HEADERS)
        resp.raise_for_status()
        companies = [ERPVendor(**c) for c in resp.json()]
        logger.info("Fetched %d companies from ERP", len(companies))
        return companies


async def submit_processed_invoice(
    file_name: str,
    extracted_data: dict,
    confidence_score: Optional[float] = None,
    processing_notes: Optional[str] = None,
) -> dict:
    payload = {
        "fileName": file_name,
        "extractedData": extracted_data,
    }
    if confidence_score is not None:
        payload["confidenceScore"] = confidence_score
    if processing_notes:
        payload["processingNotes"] = processing_notes

    print(payload)
    return {}
    # submit later when it's ready
    # async with httpx.AsyncClient() as client:
    #     resp = await client.post(
    #         f"{ERP_BASE_URL}/processed-invoices",
    #         json=payload,
    #         headers=_HEADERS,
    #     )
    #     resp.raise_for_status()
    #     result = resp.json()
    #     logger.info("Submitted invoice to ERP, id=%s", result.get("id"))
    #     return result
