import re
from rapidfuzz import fuzz
from models import ExtractedInvoice, ERPVendor, ValidationStatus

NAME_MATCH_THRESHOLD = 80.0


def _normalize_name(name: str) -> str:
    """Lowercase and strip punctuation for comparison."""
    return re.sub(r"[^\w\s]", "", name.lower()).strip()


def validate_invoice(
    extracted: ExtractedInvoice,
    companies: list[ERPVendor],
) -> tuple[ValidationStatus, list[str], str | None, float]:
    """Cross-reference extracted data against ERP company records.

    Uses exact matching on Tax ID and fuzzy matching on vendor name.
    Returns (status, discrepancies, matched_vendor_id).
    """
    discrepancies: list[str] = []
    tax_match: ERPVendor | None = None
    name_match: ERPVendor | None = None
    name_score = 0.0

    found_invoice_tax_id = extracted.vendorTaxId is not None
    match_score = 0
    # Exact match on Tax ID
    if found_invoice_tax_id:
        for company in companies:
            if company.taxId.lower() == extracted.vendorTaxId.lower():
                tax_match = company
                match_score = 100
                break

    # Fuzzy match on vendor name
    if extracted.vendorName:
        ext_norm = _normalize_name(extracted.vendorName)
        best_score = 0.0
        best_company: ERPVendor | None = None
        for company in companies:
            erp_norm = _normalize_name(company.name)
            score = fuzz.token_set_ratio(ext_norm, erp_norm)
            if score > best_score:
                best_score = score
                best_company = company

        if best_score >= NAME_MATCH_THRESHOLD:
            name_match = best_company
            name_score = best_score
            match_score = max(match_score, name_score)

    # Reconcile both matches
    if tax_match and name_match:
        if tax_match.id == name_match.id:
            return ValidationStatus.PENDING, [], tax_match.id, match_score
        discrepancies.append(
            f"Tax ID matches '{tax_match.name}' but vendor name best matches "
            f"'{name_match.name}' with score {name_score:.0f}%)"
        )
        return ValidationStatus.FLAGGED, discrepancies, tax_match.id, 0

    if tax_match and not name_match:
        if extracted.vendorName:
            discrepancies.append(
                f"Vendor name '{extracted.vendorName}' not found in ERP "
                f"(no match above a score of {NAME_MATCH_THRESHOLD:.0f}% threshold)"
            )
        # not sure if this should be pending or flagged
        return ValidationStatus.FLAGGED, discrepancies, tax_match.id, match_score

    if name_match and not tax_match:
        if not found_invoice_tax_id:
            discrepancies.append(
                f"Tax ID not found in invoice PDF file; "
                f"vendor name matches '{name_match.name}' with score "
                f"{name_score:.0f}%"
            )
            return ValidationStatus.PENDING, discrepancies, name_match.id, match_score
        else:
            discrepancies.append(
                f"Tax ID {extracted.vendorTaxId} not found in ERP; "
                f"vendor name matches '{name_match.name}' with score "
                f"{name_score:.0f}"
            )
            return ValidationStatus.FLAGGED, discrepancies, name_match.id, match_score

    discrepancies.append(
        "No matching vendor found in ERP: neither Tax ID nor vendor name matched"
    )
    return ValidationStatus.FLAGGED, discrepancies, None, match_score
