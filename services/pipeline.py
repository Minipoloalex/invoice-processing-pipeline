import uuid
import logging
from datetime import datetime, timezone
from models import ProcessedInvoice, ExtractedInvoice, ValidationStatus
from services.pdf_extractor import extract_invoice_data
from services.erp_client import fetch_companies, submit_processed_invoice
from services.validator import validate_invoice

logger = logging.getLogger(__name__)


async def process_invoice(pdf_bytes: bytes, filename: str) -> ProcessedInvoice:
    # 1. Extract structured data from PDF via LLM OCR
    extracted: ExtractedInvoice = await extract_invoice_data(pdf_bytes, filename)

    # 2. Fetch vendor records from ERP
    companies = await fetch_companies()

    # 3. Validate extracted data against ERP records
    status, discrepancies, matched_vendor_id, score = validate_invoice(
        extracted, companies
    )

    # 4. Build notes describing validation outcome
    notes = f"Validation: {status.value}"
    if discrepancies:
        notes += " | " + "; ".join(discrepancies)

    # 5. Submit processed invoice to ERP
    erp_data = extracted.model_dump(mode="json", exclude_none=True)
    erp_response = await submit_processed_invoice(
        file_name=filename,
        extracted_data=erp_data,
        processing_notes=notes,
    )

    # 6. Assemble the final ProcessedInvoice
    now = datetime.now(timezone.utc).isoformat()
    invoice = ProcessedInvoice(
        id=str(uuid.uuid4()),
        file_name=filename,
        extracted_data=extracted,
        validation_status=status,
        validation_errors=discrepancies,
        erp_vendor_id=matched_vendor_id,
        erp_submission_id=erp_response.get("id"),
        confidence_score=score,
        created_at=now,
    )

    logger.info(
        "Processed invoice %s: status=%s, erp_id=%s",
        invoice.id, status.value, invoice.erp_submission_id,
    )
    return invoice
