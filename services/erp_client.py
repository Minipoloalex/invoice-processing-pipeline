import httpx
import logging
from models import ERPVendor, ProcessedInvoice
from config import ERP_API_KEY, ERP_BASE_URL

logger = logging.getLogger(__name__)

_HEADERS = {"X-ERP-API-Key": ERP_API_KEY}


async def fetch_companies() -> list[ERPVendor]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{ERP_BASE_URL}/companies", headers=_HEADERS)
        resp.raise_for_status()
        companies = [ERPVendor(**c) for c in resp.json()]
        logger.info("Fetched %d companies from ERP", len(companies))
        return companies


async def submit_processed_invoice(invoice: ProcessedInvoice) -> dict:
    payload = invoice.model_dump(mode="json", exclude_none=True)
    payload.pop("id", None)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ERP_BASE_URL}/processed-invoices",
            json=payload,
            headers=_HEADERS,
        )
        resp.raise_for_status()
        result = resp.json()
        logger.info("Submitted invoice to ERP, id=%s", result.get("id"))
        return result


async def fetch_processed_invoices() -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ERP_BASE_URL}/processed-invoices",
            headers=_HEADERS,
        )
        resp.raise_for_status()
        return resp.json()
