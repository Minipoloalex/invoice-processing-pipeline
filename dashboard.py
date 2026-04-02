import os
import streamlit as st
import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Invoice Dashboard",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Custom CSS (FinTech aesthetic) -------------------------------------------
st.markdown(
    """
<style>
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 28px 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kpi-value {
        font-size: 2.6rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #6b7280;
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
    .badge-verified {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .badge-flagged {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .cell-match {
        background: #f0fdf4;
        border-left: 3px solid #22c55e;
        padding: 6px 10px;
        margin-bottom: 4px;
        border-radius: 4px;
    }
    .cell-mismatch {
        background: #fef2f2;
        border-left: 3px solid #ef4444;
        padding: 6px 10px;
        margin-bottom: 4px;
        border-radius: 4px;
    }
    .comparison-label {
        font-size: 0.75rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .invoice-row {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 8px;
        background: #ffffff;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# -- API helpers ---------------------------------------------------------------
def fetch_invoices():
    resp = httpx.get(f"{API_BASE_URL}/api/invoices", timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_companies():
    resp = httpx.get(f"{API_BASE_URL}/api/companies", timeout=30)
    resp.raise_for_status()
    return resp.json()


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

flagged = [i for i in invoices if i["validation_status"] == "Flagged"]
verified = [i for i in invoices if i["validation_status"] == "Verified"]


# -- KPI Cards -----------------------------------------------------------------
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#111827">{total}</div>
            <div class="kpi-label">Total Processed</div>
        </div>""",
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-value" style="color:#dc2626">{len(flagged)}</div>
            <div class="kpi-label">Needs Attention</div>
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

st.divider()


# -- Sidebar filters -----------------------------------------------------------
st.sidebar.header("Filters")
status_filter = st.sidebar.selectbox("Status", ["All", "Verified", "Flagged"])
search_query = st.sidebar.text_input("Search Vendor")

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

filtered = list(invoices)
if status_filter != "All":
    filtered = [i for i in filtered if i["validation_status"] == status_filter]
if search_query:
    q = search_query.lower()
    filtered = [
        i
        for i in filtered
        if q in (i["extracted_data"].get("vendor_name") or "").lower()
    ]


# -- Invoice list --------------------------------------------------------------
st.markdown(
    f'<div class="section-title">Invoices ({len(filtered)})</div>',
    unsafe_allow_html=True,
)

for inv in filtered:
    ext = inv["extracted_data"]
    status = inv["validation_status"]
    vendor = ext.get("vendor_name") or "Unknown"
    inv_date = ext.get("invoice_date") or "N/A"
    total_amt = ext.get("total_amount")
    currency = ext.get("currency") or ""
    badge = "badge-verified" if status == "Verified" else "badge-flagged"

    with st.container():
        row_cols = st.columns([3, 2, 2, 1.5, 1])
        with row_cols[0]:
            st.markdown(f"**{vendor}**")
            st.caption(inv["file_name"])
        with row_cols[1]:
            st.text(inv_date)
        with row_cols[2]:
            amt = f"{currency} {total_amt:,.2f}" if total_amt is not None else "N/A"
            st.text(amt)
        with row_cols[3]:
            st.markdown(
                f'<span class="badge {badge}">{status}</span>',
                unsafe_allow_html=True,
            )
        with row_cols[4]:
            pdf_url = f"{API_BASE_URL}/api/invoices/{inv['file_name']}/pdf"
            st.link_button("PDF", pdf_url, use_container_width=True)

        # -- Discrepancy detail for flagged invoices --------------------------
        if status == "Flagged":
            with st.expander("Discrepancies & Comparison"):
                errors = inv.get("validation_errors", [])
                if errors:
                    for err in errors:
                        st.error(err)

                # Side-by-side comparison with ERP record
                erp_id = inv.get("erp_vendor_id")
                if erp_id and erp_id in companies_map:
                    erp = companies_map[erp_id]

                    ext_name = ext.get("vendor_name") or ""
                    ext_tax = ext.get("tax_id") or ""
                    erp_name = erp.get("name", "")
                    erp_tax = erp.get("taxId", "")

                    name_ok = ext_name.lower() == erp_name.lower()
                    tax_ok = ext_tax.lower() == erp_tax.lower()

                    st.markdown("#### Extracted vs ERP Record")
                    left, right = st.columns(2)

                    with left:
                        st.markdown("**Extracted Data**")
                        n_cls = "cell-match" if name_ok else "cell-mismatch"
                        t_cls = "cell-match" if tax_ok else "cell-mismatch"
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
                            f'<div class="{n_cls}">{erp_name}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="comparison-label">Tax ID</div>'
                            f'<div class="{t_cls}">{erp_tax}</div>',
                            unsafe_allow_html=True,
                        )

                # Full extracted JSON
                with st.expander("Raw Extracted Data"):
                    st.json(ext)

        st.markdown("<hr style='margin:4px 0;border-color:#f3f4f6'>", unsafe_allow_html=True)
