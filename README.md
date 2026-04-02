# Invoice Processing Pipeline
The project is implemented in Python, with libraries managed by `uv`.

## Tools and libraries
- `fastapi` and `uvicorn`: to build and support the backend Python API
- `httpx`: to perform asynchronous requests to the ERP API
- `google-genai` and the model `gemini-flash-lite-latest` to extract information from the invoice PDFs
- `pydantic` for model validation, both regarding the backend API and the LLM extraction call.
- `rapidfuzz` for matching company names to extracted vendor names.
- `streamlit` and `streamlit-authenticator` for the implementation of the dashboard and authentication.

## Project Structure
```
services/
    erp_client.py       # communicates with the ERP database
    pdf_extractor.py    # handles extracting information from an invoice PDF
    pipeline.py 
    validator.py        # validates extracted information against company database data
config.py               # environment variables
dashboard.py            # streamlit dashboard
main.py                 # main backend API
models.py               # pydantic models
```


## Pipeline
The pipeline starts and ends at the dashboard, which sends the uploaded file to the backend, retrieving the resulting invoice information.

The main pipeline for extracting information from invoice PDF files is shown in the image and code snippet below:

A shortened version from `services/pipeline.py`:
```python
async def process_invoice(pdf_bytes: bytes, filename: str) -> ProcessedInvoice:
    # Extract structured data from PDF via an LLM
    extracted: ExtractedInvoice = await extract_invoice_data(pdf_bytes, filename)

    # Normalize extracted fields
    ... # omitted for brevity

    # Fetch vendor records from ERP
    companies = await fetch_companies()

    # Validate extracted data against ERP records
    status, discrepancies, matched_vendor_id, score = validate_invoice(
        extracted, companies
    )

    # Build enriched ExtractedData with validation results
    enriched_data = ExtractedData(
        **extracted.model_dump(),
        erpVendorId=matched_vendor_id,
        validationStatus=status,
        validationErrors=discrepancies,
    )

    # Build notes describing validation outcome
    notes = ... # omitted for brevity

    # Submit processed invoice to ERP
    erp_data = enriched_data.model_dump(mode="json", exclude_none=True)
    await submit_processed_invoice(
        file_name=filename,
        extracted_data=erp_data,
        processing_notes=notes,
    )

    # Assemble the final ProcessedInvoice
    invoice = ProcessedInvoice(
        id=str(uuid.uuid4()),
        fileName=filename,
        extractedData=enriched_data,
        confidenceScore=score,
        processingNotes=notes,
    )

    logger.info(
        "Processed invoice %s: status=%s",
        invoice.id, status.value,
    )
    return invoice
```

## Design Choices
For controlling the state of an invoice, the implementation uses 4 possible status:
- Flagged:
    - mismatch between tax id and company found during extraction or none found
    - an issue flagged by an analyst
- Pending: extraction process, pending review from an analyst
- Verified: analyst as verified the invoice information, making it ready for payment
- Complete (paid): invoice marked by a manager as paid


## Future work
Although not implemented, there should be support for modifying an invoice's status. Modifying the invoice's extracted information would also be crucial for fixing inconsistencies and ensuring the system works as the user intends. Allowing deletion of invoices would also give more flexibility.

Let the user toggle a configuration to show all of the invoices, or just the "active" (recent) invoices.

