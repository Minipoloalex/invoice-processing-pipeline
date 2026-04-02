import json
import logging
from google import genai
from models import ExtractedInvoice
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are an invoice data extraction assistant. Extract the following fields from \
this invoice PDF file and return them as a JSON object with these exact keys:
- "vendorName": The name of the vendor/company issuing the invoice
- "vendorTaxId": The tax ID, VAT number, or registration number of the vendor
- "invoiceNumber": The invoice number or reference
- "invoiceDate": Invoice date in YYYY-MM-DD format
- "dueDate": Payment due date in YYYY-MM-DD format
- "currency": Currency code (USD, EUR, INR, etc.)
- "subtotal": Subtotal before tax (number)
- "taxAmount": Total tax amount (number)
- "totalAmount": Total amount including tax (number)
- "lineItems": Array of objects, each with keys: "description", "quantity", "unitPrice", "total"

Return ONLY valid JSON. Don't include fields you cannot find."""

async def extract_invoice_data(pdf_bytes: bytes, filename: str) -> ExtractedInvoice:
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            genai.types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            "Extract the invoice details.",
        ],
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedInvoice,
        ),
    )

    response_text = response.text.strip()

    # Strip markdown code fences if the model wraps them
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    data = json.loads(response_text)
    logger.info("Extracted invoice data from %s: %s", filename, data)
    return ExtractedInvoice.model_validate(data)
