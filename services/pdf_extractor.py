import base64
import json
import logging
import anthropic
from models import ExtractedInvoice
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are an invoice data extraction assistant. Extract the following fields from \
this invoice and return them as a JSON object with these exact keys:
- "vendor_name": The name of the vendor/company issuing the invoice
- "tax_id": The tax ID, VAT number, or registration number of the vendor
- "invoice_number": The invoice number or reference
- "invoice_date": Invoice date in YYYY-MM-DD format
- "due_date": Payment due date in YYYY-MM-DD format
- "currency": Currency code (USD, EUR, INR, etc.)
- "subtotal": Subtotal before tax (number)
- "tax_amount": Total tax amount (number)
- "total_amount": Total amount including tax (number)
- "line_items": Array of objects, each with keys: "description", "quantity", "unit_price", "total"

Return ONLY valid JSON. Use null for any fields you cannot find."""


async def extract_invoice_data(pdf_bytes: bytes, filename: str) -> ExtractedInvoice:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": EXTRACTION_PROMPT},
                ],
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code fences if the model wraps them
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    data = json.loads(response_text)
    logger.info("Extracted invoice data from %s: %s", filename, data)
    return ExtractedInvoice.model_validate(data)
