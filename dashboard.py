import os
import time
import yaml
import streamlit as st
import streamlit_authenticator as stauth
import httpx

from config import DASHBOARD_API_KEY
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Invoice Dashboard",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Custom CSS -------------------------------------------
st.markdown(
    """
<style>
    .kpi-card {
        background: rgba(128, 128, 128, 0.1);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 28px 20px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .kpi-value {
        font-size: 2.6rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: var(--text-color);
        opacity: 0.6;
        margin-top: 6px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.82rem;
        letter-spacing: 0.3px;
    }
    .badge-flagged {
        background: rgba(239,68,68,0.15);
        color: #ef4444;
        border: 1px solid rgba(239,68,68,0.4);
    }
    .badge-pending {
        background: rgba(234,179,8,0.15);
        color: #eab308;
        border: 1px solid rgba(234,179,8,0.4);
    }
    .badge-verified {
        background: rgba(34,197,94,0.15);
        color: #22c55e;
        border: 1px solid rgba(34,197,94,0.4);
    }
    .badge-complete {
        background: rgba(107,114,128,0.15);
        color: var(--text-color);
        opacity: 0.7;
        border: 1px solid rgba(107,114,128,0.3);
    }
    .cell-match {
        background: rgba(34,197,94,0.1);
        border-left: 3px solid #22c55e;
        padding: 6px 10px;
        margin-bottom: 4px;
        border-radius: 4px;
        color: var(--text-color);
    }
    .cell-mismatch {
        background: rgba(239,68,68,0.1);
        border-left: 3px solid #ef4444;
        padding: 6px 10px;
        margin-bottom: 4px;
        border-radius: 4px;
        color: var(--text-color);
    }
    .comparison-label {
        font-size: 0.75rem;
        color: var(--text-color);
        opacity: 0.5;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-color);
        margin-bottom: 12px;
    }
    .finance-value {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--text-color);
    }
    .table-header {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-color);
        opacity: 0.5;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# -- Authentication ------------------------------------------------------------
with open("credentials.yaml") as f:
    config = yaml.safe_load(f)

authenticator = stauth.Authenticate(
    credentials=config["credentials"],
    cookie_name=config["cookie"]["name"],
    cookie_key=config["cookie"]["key"],
    cookie_expiry_days=config["cookie"]["expiry_days"],
)

authenticator.login(location="main")

auth_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")

if auth_status is False:
    st.error("Username or password is incorrect")
    st.stop()
elif auth_status is None:
    st.stop()

# -- API helpers (with API key) ------------------------------------------------
_headers = {"X-API-Key": DASHBOARD_API_KEY} if DASHBOARD_API_KEY else {}


def fetch_invoices():
    resp = httpx.get(f"{API_BASE_URL}/api/invoices", headers=_headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_companies():
    resp = httpx.get(f"{API_BASE_URL}/api/companies", headers=_headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def upload_invoice(pdf_bytes: bytes, filename: str):
    return httpx.post(
        f"{API_BASE_URL}/api/upload",
        files={"file": (filename, pdf_bytes, "application/pdf")},
        headers=_headers,
        timeout=120,
    )


def fetch_invoice_pdf(file_name: str):
    return httpx.get(
        f"{API_BASE_URL}/api/invoices/{file_name}/pdf",
        headers=_headers,
        timeout=30,
    )


# -- Data loading --------------------------------------------------------------
@st.cache_data(ttl=30)
def load_invoices():
    return fetch_invoices()


@st.cache_data(ttl=60)
def load_companies():
    try:
        companies = fetch_companies()
        return {c["id"]: c for c in companies}
    except Exception:
        return {}


data = load_invoices()
invoices = data.get("items", [])
total = data.get("total", 0)
companies_map = load_companies()

flagged = [i for i in invoices if i["extractedData"]["validationStatus"] == "Flagged"]
pending = [i for i in invoices if i["extractedData"]["validationStatus"] == "Pending"]
verified = [i for i in invoices if i["extractedData"]["validationStatus"] == "Verified"]
complete = [i for i in invoices if i["extractedData"]["validationStatus"] == "Complete"]

# -- KPI Cards -----------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#dc2626">{len(flagged)}</div>
            <div class="kpi-label">Needs Attention</div>
        </div>""",
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#ca8a04">{len(pending)}</div>
            <div class="kpi-label">Pending Review</div>
        </div>""",
        unsafe_allow_html=True,
    )

with kpi3:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#16a34a">{len(verified)}</div>
            <div class="kpi-label">Ready for Payment</div>
        </div>""",
        unsafe_allow_html=True,
    )

with kpi4:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#6b7280">{len(complete)}</div>
            <div class="kpi-label">Paid</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()

# -- Sidebar: logout, upload, filters ------------------------------------------
with st.sidebar:
    authenticator.logout("Logout", "main")
    if st.session_state.get("authentication_status"):
        st.write(f"Logged in as **{st.session_state.get('name')}**")

    st.divider()

    # -- Upload section --------------------------------------------------------
    st.subheader("Submit Invoices")
    if "upload_counter" not in st.session_state:
        st.session_state["upload_counter"] = 0
    uploaded_files = st.file_uploader(
        "Upload PDF invoices",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"invoice_upload_{st.session_state['upload_counter']}",
    )

    if uploaded_files:
        if st.button("Process Invoices", use_container_width=True, type="primary"):
            successes = 0
            failures = 0
            for f in uploaded_files:
                with st.spinner(f"Processing {f.name}..."):
                    try:
                        resp = upload_invoice(f.getvalue(), f.name)
                        resp.raise_for_status()
                        result = resp.json()

                        ext = result["extractedData"]
                        status = ext["validationStatus"]
                        vendor = ext.get("vendorName") or "Unknown"
                        badge = f"badge-{status.lower()}"

                        st.success(f"{f.name} processed successfully!")
                        successes += 1
                    except httpx.HTTPStatusError as e:
                        st.error(f"{f.name}: server error ({e.response.text})")
                        failures += 1
                    except Exception as e:
                        st.error(f"{f.name}: failed ({e})")
                        failures += 1

            if successes:
                st.session_state["upload_counter"] += 1
                time.sleep(2)   # Give time for the user to see the success/error message
                st.rerun()

    st.divider()

    # -- Filters ---------------------------------------------------------------
    st.subheader("Filters")
    status_filter = st.selectbox("Status", ["All", "Flagged", "Pending", "Verified", "Complete"])
    search_query = st.text_input("Search Vendor")

    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Apply filters
filtered = list(invoices)
if status_filter != "All":
    filtered = [i for i in filtered if i["extractedData"]["validationStatus"] == status_filter]
if search_query:
    q = search_query.lower()
    filtered = [
        i
        for i in filtered
        if q in (i["extractedData"].get("vendorName") or "").lower()
    ]

# -- Invoice list --------------------------------------------------------------
st.markdown(
    f"### Invoices ({len(filtered)})"
)

# Sort by due date, then by issue date (None/missing dates go first)
filtered.sort(key=lambda i:
    (
        i["extractedData"].get("dueDate") or i["extractedData"].get("issueDate") or "1970-01-01",
        i["extractedData"].get("issueDate") or "1970-01-01",
    )
)

COL_WIDTHS = [3, 1.5, 1.5, 2, 2, 1.5, 1]
COL_LABELS = ["Vendor", "Inv. Number", "Issue Date", "Due Date", "Total", "Status", ""]

for inv in filtered:
    ext = inv["extractedData"]
    status = ext["validationStatus"]
    vendor = ext.get("vendorName") or "Unknown"
    inv_number = ext.get("invoiceNumber") or "N/A"
    inv_date = ext.get("invoiceDate") or "N/A"
    due_date = ext.get("dueDate") or "N/A"
    total_amt = ext.get("totalAmount")
    currency = ext.get("currency") or ""
    badge = f"badge-{status.lower()}"

    with st.container():
        header_cols = st.columns(COL_WIDTHS)
        for col, label in zip(header_cols, COL_LABELS):
            with col:
                st.markdown(f'<div class="table-header">{label}</div>', unsafe_allow_html=True)

        row_cols = st.columns(COL_WIDTHS)
        with row_cols[0]:
            st.markdown(f"**{vendor}**")
        with row_cols[1]:
            st.text(inv_number)
        with row_cols[2]:
            st.text(inv_date)
        with row_cols[3]:
            st.text(due_date)
        with row_cols[4]:
            amt = f"{currency} {total_amt:,.2f}" if total_amt is not None else "N/A"
            st.text(amt)
        with row_cols[5]:
            st.markdown(
                f'<span class="badge {badge}">{status}</span>',
                unsafe_allow_html=True,
            )
        with row_cols[6]:
            pdf_resp = fetch_invoice_pdf(inv["fileName"])
            if pdf_resp.status_code == 200:
                st.download_button(
                    "PDF",
                    data=pdf_resp.content,
                    file_name=inv["fileName"],
                    mime="application/pdf",
                    key=f"dl_{inv['id']}",
                    use_container_width=True,
                )

        # -- Detail expander for all invoices --------------------------
        with st.expander("Details"):
            errors = ext.get("validationErrors", [])
            if errors:
                for err in errors:
                    if status == "Flagged":
                        st.error(err)
                    else:
                        st.warning(err)

            erp_id = ext.get("erpVendorId")
            erp = companies_map.get(erp_id) if erp_id else None

            ext_name = ext.get("vendorName") or ""
            ext_tax = ext.get("vendorTaxId") or ""
            erp_name = erp.get("name", "") if erp else ""
            erp_tax = erp.get("taxId", "") if erp else ""

            name_ok = bool(erp) and ext_name.lower() == erp_name.lower()
            tax_ok = bool(erp) and ext_tax.lower() == erp_tax.lower()

            st.markdown("#### Extracted vs ERP Record")
            left, right = st.columns(2)

            n_cls = "cell-match" if name_ok else "cell-mismatch"
            t_cls = "cell-match" if tax_ok else "cell-mismatch"

            with left:
                st.markdown("**Extracted Data**")
                st.markdown(
                    f'<div class="comparison-label">Vendor Name</div>'
                    f'<div class="{n_cls}">{ext_name or "N/A"}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="comparison-label">Tax ID</div>'
                    f'<div class="{t_cls}">{ext_tax or "N/A"}</div>',
                    unsafe_allow_html=True,
                )

            with right:
                st.markdown("**ERP Record**")
                st.markdown(
                    f'<div class="comparison-label">Vendor Name</div>'
                    f'<div class="{n_cls}">{erp_name or "N/A"}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="comparison-label">Tax ID</div>'
                    f'<div class="{t_cls}">{erp_tax or "N/A"}</div>',
                    unsafe_allow_html=True,
                )

            # -- Financial breakdown -----------------------------------------
            st.markdown("<div style='margin-top: 24px'></div>", unsafe_allow_html=True)
            cur = ext.get("currency") or ""
            fin_cols = st.columns(3)
            with fin_cols[0]:
                sub = ext.get("subtotal")
                st.markdown(f'<div class="comparison-label">Subtotal</div>'
                            f'<div class="finance-value">{f"{cur} {sub:,.2f}" if sub is not None else "N/A"}</div>',
                            unsafe_allow_html=True)
            with fin_cols[1]:
                tax = ext.get("taxAmount")
                st.markdown(f'<div class="comparison-label">Tax</div>'
                            f'<div class="finance-value">{f"{cur} {tax:,.2f}" if tax is not None else "N/A"}</div>',
                            unsafe_allow_html=True)
            with fin_cols[2]:
                tot = ext.get("totalAmount")
                st.markdown(f'<div class="comparison-label">Total</div>'
                            f'<div class="finance-value">{f"{cur} {tot:,.2f}" if tot is not None else "N/A"}</div>',
                            unsafe_allow_html=True)

            line_items = ext.get("lineItems") or []
            if line_items:
                st.markdown("#### Items")
                li_header = st.columns([0.5, 4, 1, 1.5, 1.5])
                for col, label, align in zip(
                    li_header,
                    ["", "Description", "Qty", "Unit Price", "Total"],
                    ["", "", "", "right", "right"],
                ):
                    with col:
                        align_style = f"text-align:{align};" if align else ""
                        st.markdown(f'<div class="table-header" style="{align_style}">{label}</div>', unsafe_allow_html=True)
                for idx, item in enumerate(line_items, 1):
                    li_cols = st.columns([0.5, 4, 1, 1.5, 1.5])
                    with li_cols[0]:
                        st.text(str(idx))
                    with li_cols[1]:
                        st.text(item.get("description") or "N/A")
                    with li_cols[2]:
                        qty = item.get("quantity")
                        st.text(f"{qty:,.0f}" if qty is not None else "N/A")
                    with li_cols[3]:
                        up = item.get("unitPrice")
                        st.markdown(f'<div style="text-align:right">{f"{cur} {up:,.2f}" if up is not None else "N/A"}</div>', unsafe_allow_html=True)
                    with li_cols[4]:
                        t = item.get("total")
                        st.markdown(f'<div style="text-align:right">{f"{cur} {t:,.2f}" if t is not None else "N/A"}</div>', unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 16px'></div>", unsafe_allow_html=True)
            with st.expander("Raw Extracted Data"):
                st.json(ext)

    st.markdown(
        "<hr style='margin:4px 0;border-color:var(--border-color)'>", unsafe_allow_html=True
    )
