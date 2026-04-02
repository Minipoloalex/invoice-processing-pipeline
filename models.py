from enum import Enum
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class ValidationStatus(str, Enum):
    VERIFIED = "Verified"
    FLAGGED = "Flagged"


class InvoiceItem(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class ExtractedInvoice(BaseModel):  # internal
    vendor_name: Optional[str] = None
    tax_id: Optional[str] = None    # this looks like something that should be cross-referenced
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    line_items: list[InvoiceItem] = Field(default_factory=list)


class ERPVendor(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    id: str
    name: str
    tax_id: str
    address: Optional[str] = None
    country: Optional[str] = None
    created_at: Optional[str] = None


class ProcessedInvoice(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    id: str
    file_name: str
    extracted_data: ExtractedInvoice
    validation_status: ValidationStatus
    validation_errors: list[str] = Field(default_factory=list)
    erp_vendor_id: Optional[str] = None
    erp_submission_id: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: str


class InvoiceListResponse(BaseModel):
    items: list[ProcessedInvoice]
    total: int
