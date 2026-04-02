import uuid
import logging
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

    # 4. Update extracted data with validation results
    extracted.validationStatus = status
    extracted.validationErrors = discrepancies
    extracted.erpVendorId = matched_vendor_id

    # 5. Build notes describing validation outcome
    notes = f"Validation: {status.value}"
    if discrepancies:
        notes += " | " + "; ".join(discrepancies)

    # 6. Submit processed invoice to ERP
    erp_data = extracted.model_dump(mode="json", exclude_none=True)
    await submit_processed_invoice(
        file_name=filename,
        extracted_data=erp_data,
        processing_notes=notes,
    )

    # 7. Assemble the final ProcessedInvoice
    invoice = ProcessedInvoice(
        id=str(uuid.uuid4()),
        fileName=filename,
        extractedData=extracted,
        confidenceScore=score,
        processingNotes=notes,
    )

    logger.info(
        "Processed invoice %s: status=%s",
        invoice.id, status.value,
    )
    return invoice
