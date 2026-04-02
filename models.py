from enum import Enum
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    FLAGGED = "Flagged"
    PENDING = "Pending"
    VERIFIED = "Verified"
    COMPLETE = "Complete"


class InvoiceItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unitPrice: Optional[float] = None
    total: Optional[float] = None


class ExtractedInvoice(BaseModel):  # internal (output from model)
    vendorName: Optional[str] = None
    vendorTaxId: Optional[str] = None
    invoiceNumber: Optional[str] = None
    invoiceDate: Optional[date] = None
    dueDate: Optional[date] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    taxAmount: Optional[float] = None
    totalAmount: Optional[float] = None
    lineItems: list[InvoiceItem] = Field(default_factory=list)


class ExtractedData(ExtractedInvoice):  # final information (after getting information from ERP DB)
    erpVendorId: Optional[str] = None
    validationStatus: ValidationStatus
    validationErrors: list[str] = Field(default_factory=list)


class ERPVendor(BaseModel):
    id: str
    name: str
    taxId: str
    address: Optional[str] = None
    country: Optional[str] = None
    createdAt: Optional[str] = None


class ProcessedInvoice(BaseModel):
    id: str
    fileName: str
    extractedData: ExtractedData
    confidenceScore: Optional[float] = None
    processingNotes: Optional[str] = None


class InvoiceListResponse(BaseModel):
    items: list[ProcessedInvoice]
    total: int
