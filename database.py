import aiosqlite
from models import (
    ProcessedInvoice,
    ExtractedInvoice,
    InvoiceListResponse,
)
from config import DATABASE_PATH

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    fileName TEXT NOT NULL,
    extractedData TEXT NOT NULL,
    confidenceScore REAL,
    processingNotes TEXT
)
"""


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(_CREATE_TABLE)
        await db.commit()


def _row_to_invoice(row: aiosqlite.Row) -> ProcessedInvoice:
    return ProcessedInvoice(
        id=row["id"],
        fileName=row["fileName"],
        extractedData=ExtractedInvoice.model_validate_json(row["extractedData"]),
        confidenceScore=row["confidenceScore"],
        processingNotes=row["processingNotes"],
    )


async def save_invoice(invoice: ProcessedInvoice) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO invoices
               (id, fileName, extractedData, confidenceScore, processingNotes)
               VALUES (?, ?, ?, ?, ?)""",
            (
                invoice.id,
                invoice.fileName,
                invoice.extractedData.model_dump_json(),
                invoice.confidenceScore,
                invoice.processingNotes,
            ),
        )
        await db.commit()


async def get_invoices() -> InvoiceListResponse:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM invoices ORDER BY rowid DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            items = [_row_to_invoice(row) for row in rows]
            return InvoiceListResponse(items=items, total=len(items))
