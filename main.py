import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, UploadFile, File, Header, HTTPException
from fastapi.responses import FileResponse
from services.pipeline import process_invoice
from services.erp_client import fetch_companies, fetch_processed_invoices
from models import InvoiceListResponse, ProcessedInvoice, ExtractedData
from config import DASHBOARD_API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

PDF_DIR = Path("invoice_pdfs")


async def verify_api_key(x_api_key: str | None = Header(None)):
    if DASHBOARD_API_KEY:
        if not x_api_key or x_api_key != DASHBOARD_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    PDF_DIR.mkdir(exist_ok=True)
    logger.info("Application started")
    yield


app = FastAPI(
    title="Invoice Processing API",
    description="Automated invoice extraction, validation, and ERP submission",
    version="0.1.0",
    lifespan=lifespan,
)


@app.post(
    "/api/upload",
    response_model=ProcessedInvoice,
    summary="Upload and process a PDF invoice",
)
async def upload_invoice(
    file: UploadFile = File(...),
    _api_key: str = Depends(verify_api_key),
):
    """Accept a PDF invoice, extract data via LLM, validate against ERP,
    submit to ERP, and return the processed invoice."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        invoice = await process_invoice(pdf_bytes, file.filename)
    except Exception as e:
        logger.exception("Invoice processing failed for %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    # Persist the PDF for later preview
    (PDF_DIR / file.filename).write_bytes(pdf_bytes)

    logger.info("Processed invoice %s", invoice.fileName)
    return invoice


@app.get(
    "/api/invoices",
    response_model=InvoiceListResponse,
    summary="List all processed invoices",
)
async def list_invoices(_api_key: str = Depends(verify_api_key)):
    """Retrieve all processed invoices from the ERP."""
    data = await fetch_processed_invoices()
    items = [
        ProcessedInvoice(
            id=item["id"],
            fileName=item.get("fileName", ""),
            extractedData=ExtractedData.model_validate(item["extractedData"]),
            confidenceScore=item.get("confidenceScore"),
            processingNotes=item.get("processingNotes"),
        )
        for item in data.get("items", [])
    ]
    return InvoiceListResponse(items=items, total=data.get("total", len(items)))


@app.get("/api/companies", summary="List ERP vendor companies")
async def list_companies(_api_key: str = Depends(verify_api_key)):
    """Proxy endpoint: fetch vendor records from the external ERP."""
    companies = await fetch_companies()
    return [c.model_dump() for c in companies]


@app.get(
    "/api/invoices/{file_name:path}/pdf",
    summary="Serve the original PDF for an invoice",
)
async def get_invoice_pdf(
    file_name: str,
    _api_key: str = Depends(verify_api_key),
):
    pdf_path = PDF_DIR / file_name
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type="application/pdf", filename=file_name)
