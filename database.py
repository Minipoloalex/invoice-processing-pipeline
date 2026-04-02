import aiosqlite
import json
from typing import Optional
from models import (
    ProcessedInvoice,
    ExtractedInvoice,
    ValidationStatus,
    InvoiceListResponse,
)
from config import DATABASE_PATH

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    extracted_data TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    validation_errors TEXT NOT NULL,
    erp_vendor_id TEXT,
    erp_submission_id TEXT,
    confidence_score REAL,
    created_at TEXT NOT NULL
)
"""


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(_CREATE_TABLE)
        await db.commit()


def _row_to_invoice(row: aiosqlite.Row) -> ProcessedInvoice:
    return ProcessedInvoice(
        id=row["id"],
        file_name=row["file_name"],
        extracted_data=ExtractedInvoice.model_validate_json(row["extracted_data"]),
        validation_status=ValidationStatus(row["validation_status"]),
        validation_errors=json.loads(row["validation_errors"]),
        erp_vendor_id=row["erp_vendor_id"],
        erp_submission_id=row["erp_submission_id"],
        confidence_score=row["confidence_score"],
        created_at=row["created_at"],
    )


async def save_invoice(invoice: ProcessedInvoice) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO invoices
               (id, file_name, extracted_data, validation_status,
                validation_errors, erp_vendor_id, erp_submission_id,
                confidence_score, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                invoice.id,
                invoice.file_name,
                invoice.extracted_data.model_dump_json(),
                invoice.validation_status.value,
                json.dumps(invoice.validation_errors),
                invoice.erp_vendor_id,
                invoice.erp_submission_id,
                invoice.confidence_score,
                invoice.created_at,
            ),
        )
        await db.commit()


async def get_invoices() -> InvoiceListResponse:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM invoices ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            items = [_row_to_invoice(row) for row in rows]
            return InvoiceListResponse(items=items, total=len(items))
