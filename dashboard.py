import os
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
print(data)
invoices = data.get("items", [])
total = data.get("total", 0)
companies_map = load_companies()

flagged = [i for i in invoices if i["extractedData"]["validationStatus"] == "Flagged"]
verified = [i for i in invoices if i["extractedData"]["validationStatus"] == "Verified"]

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

# -- Sidebar: logout, upload, filters ------------------------------------------
with st.sidebar:
    authenticator.logout("Logout", "main")
    if st.session_state.get("authentication_status"):
        st.write(f"Logged in as **{st.session_state.get('name')}**")

    st.divider()

    # -- Upload section --------------------------------------------------------
    st.subheader("Submit Invoice")
    uploaded_file = st.file_uploader(
        "Upload a PDF invoice",
        type=["pdf"],
        key="invoice_upload",
    )

    if uploaded_file is not None:
        if st.button("Process Invoice", use_container_width=True, type="primary"):
            with st.spinner("Extracting and validating invoice..."):
                try:
                    resp = upload_invoice(
                        uploaded_file.getvalue(),
                        uploaded_file.name,
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    st.cache_data.clear()

                    ext = result["extractedData"]
                    status = ext["validationStatus"]
                    vendor = ext.get("vendorName") or "Unknown"
                    badge = "badge-verified" if status == "Verified" else "badge-flagged"

                    st.markdown(
                        f'<span class="badge {badge}">{status}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{vendor}**")
                    amt = ext.get("totalAmount")
                    cur = ext.get("currency", "")
                    if amt is not None:
                        st.write(f"Amount: {cur} {amt:,.2f}")

                    errors = ext.get("validationErrors", [])
                    if errors:
                        for err in errors:
                            st.warning(err)

                    st.success("Invoice processed successfully!")
                    st.rerun()
                except httpx.HTTPStatusError as e:
                    st.error(f"Server error: {e.response.text}")
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    st.divider()

    # -- Filters ---------------------------------------------------------------
    st.subheader("Filters")
    status_filter = st.selectbox("Status", ["All", "Verified", "Flagged"])
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
    f'<div class="section-title">Invoices ({len(filtered)})</div>',
    unsafe_allow_html=True,
)

for inv in filtered:
    ext = inv["extractedData"]
    status = ext["validationStatus"]
    vendor = ext.get("vendorName") or "Unknown"
    inv_date = ext.get("invoiceDate") or "N/A"
    total_amt = ext.get("totalAmount")
    currency = ext.get("currency") or ""
    badge = "badge-verified" if status == "Verified" else "badge-flagged"

    with st.container():
        row_cols = st.columns([3, 2, 2, 1.5, 1])
        with row_cols[0]:
            st.markdown(f"**{vendor}**")
            st.caption(inv["fileName"])
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
            pdf_url = f"{API_BASE_URL}/api/invoices/{inv['fileName']}/pdf"
            st.link_button("PDF", pdf_url, use_container_width=True)

        # -- Discrepancy detail for flagged invoices --------------------------
        if status == "Flagged":
            with st.expander("Discrepancies & Comparison"):
                errors = ext.get("validationErrors", [])
                if errors:
                    for err in errors:
                        st.error(err)

                erp_id = ext.get("erpVendorId")
                if erp_id and erp_id in companies_map:
                    erp = companies_map[erp_id]

                    ext_name = ext.get("vendorName") or ""
                    ext_tax = ext.get("vendorTaxId") or ""
                    erp_name = erp.get("name", "")
                    erp_tax = erp.get("taxId", "")

                    name_ok = ext_name.lower() == erp_name.lower()
                    tax_ok = ext_tax.lower() == erp_tax.lower()

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
                            f'<div class="{n_cls}">{erp_name}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="comparison-label">Tax ID</div>'
                            f'<div class="{t_cls}">{erp_tax}</div>',
                            unsafe_allow_html=True,
                        )

                with st.expander("Raw Extracted Data"):
                    st.json(ext)

    st.markdown(
        "<hr style='margin:4px 0;border-color:#f3f4f6'>", unsafe_allow_html=True
    )
