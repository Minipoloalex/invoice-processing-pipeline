import re
import logging
from models import ProcessedInvoice, ExtractedInvoice, ExtractedData
from services.pdf_extractor import extract_invoice_data
from services.erp_client import fetch_companies, submit_processed_invoice
from services.validator import validate_invoice

logger = logging.getLogger(__name__)


async def process_invoice(pdf_bytes: bytes, filename: str) -> ProcessedInvoice:
    # Extract structured data from PDF via an LLM
    extracted: ExtractedInvoice = await extract_invoice_data(pdf_bytes, filename)

    # Normalize extracted fields
    if extracted.vendorTaxId:
        # Keep only alphanumeric characters and hyphens
        extracted.vendorTaxId = re.sub(r"[^a-zA-Z0-9\-]", "", extracted.vendorTaxId).upper()

    # Fetch vendor records from ERP
    companies = await fetch_companies()

    # Validate extracted data against ERP records
    status, discrepancies, matched_vendor_id, score = validate_invoice(
        extracted, companies
    )
    score /= 100

    # Build enriched ExtractedData with validation results
    enriched_data = ExtractedData(
        **extracted.model_dump(),
        erpVendorId=matched_vendor_id,
        validationStatus=status,
        validationErrors=discrepancies,
    )

    # Build notes describing validation outcome
    notes = f"Automatically validated: {status.value}"
    if discrepancies:
        notes += " | " + "; ".join(discrepancies)

    # Build invoice
    invoice = ProcessedInvoice(
        fileName=filename,
        extractedData=enriched_data,
        confidenceScore=score,
        processingNotes=notes,
    )

    # Submit to ERP
    erp_response = await submit_processed_invoice(invoice)
    invoice.id = erp_response["id"]

    logger.info(
        "Processed invoice %s: status=%s",
        invoice.id, status.value,
    )
    return invoice
