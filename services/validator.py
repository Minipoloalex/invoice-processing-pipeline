from rapidfuzz import fuzz
from models import ExtractedInvoice, ERPVendor, ValidationStatus

NAME_MATCH_THRESHOLD = 80.0


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

    match_score = 0
    # Exact match on Tax ID
    if extracted.tax_id:
        for company in companies:
            if company.tax_id.lower() == extracted.tax_id.lower():
                tax_match = company
                match_score = 100
                break

    # Fuzzy match on vendor name
    if extracted.vendor_name:
        best_score = 0.0
        best_company: ERPVendor | None = None
        for company in companies:
            score = fuzz.token_sort_ratio(
                extracted.vendor_name.lower(),
                company.name.lower(),
            )
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
            return ValidationStatus.VERIFIED, [], tax_match.id, match_score
        discrepancies.append(
            f"Tax ID matches '{tax_match.name}' but vendor name best matches "
            f"'{name_match.name}' (score: {name_score:.0f}%)"
        )
        return ValidationStatus.FLAGGED, discrepancies, tax_match.id, match_score

    if tax_match and not name_match:
        if extracted.vendor_name:
            discrepancies.append(
                f"Vendor name '{extracted.vendor_name}' not found in ERP "
                f"(no match above {NAME_MATCH_THRESHOLD:.0f}% threshold)"
            )
        return ValidationStatus.FLAGGED, discrepancies, tax_match.id, match_score

    if name_match and not tax_match:
        discrepancies.append(
            f"Tax ID '{extracted.tax_id}' not found in ERP; "
            f"vendor name matches '{name_match.name}' by fuzzy match "
            f"(score: {name_score:.0f}%)"
        )
        return ValidationStatus.FLAGGED, discrepancies, name_match.id, match_score

    discrepancies.append(
        "No matching vendor found in ERP: neither Tax ID nor vendor name matched"
    )
    return ValidationStatus.FLAGGED, discrepancies, None, match_score
