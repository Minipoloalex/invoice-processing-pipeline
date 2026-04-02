# Objective

Build a working system that solves Portline's invoice processing problem.

Input: Invoice PDF files, available in the `invoice_pdfs` folder. The ERP API holds vendor records you'll need for validation.

Output: A deployed web application with a dashboard that lets the finance team review processed invoice data --- what's been extracted, whether it looks correct, and what needs attention.

Your processing pipeline should:

- Extract structured data from the invoice PDFs (OCR / document parsing)
- Cross-reference extracted vendor data against company records from GET /api/erp/companies
- Submit processed results back via POST /api/erp/processed-invoices

Your dashboard should make the finance team's job easier, not just display raw data.

## User Stories

- **As a finance analyst**, I want to see all processed invoices in one place with their key details, so I can quickly review what's been processed and what's still pending.

- **As a finance analyst**, I want to know if an invoice's vendor data matches our company records (name, tax ID), so I can catch discrepancies before we approve a payment.

- **As a finance manager**, I want a summary view of processing status and any flagged issues, so I know what needs my attention without checking each invoice individually.
Constraints

- Your solution must be deployed to a publicly accessible URL
- Processed invoice data must be submitted to the ERP via the API
- Invoice PDFs are available in the Materials page
- You may use any tech stack you're comfortable with
- See What We're Looking For to understand how your solution will be evaluated
