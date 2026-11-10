"""Financial Statement AI Analyzer — deployment-preparation MVP."""
import hashlib

import fitz
import pandas as pd
import streamlit as st

from filing_parser import find_filing_sections
from financial_metrics import extract_financial_metrics
from financial_visualizations import (
    validate_chart_data,
    create_revenue_chart,
    create_income_chart,
    create_comparison_chart,
    create_margin_chart,
)
from source_utils import (
    get_page_text,
    find_source_context,
    build_cited_document,
    validate_document,
)

st.set_page_config(page_title="Financial Statement AI Analyzer", page_icon="📊", layout="wide")


def learning_guide():
    statement = st.selectbox("Learn about a financial statement", [
        "Income Statement", "Balance Sheet", "Cash Flow Statement"
    ])
    if statement == "Income Statement":
        st.write("Revenue, expenses, and profit over a reporting period.")
        st.latex(r"\text{Net Income} = \text{Revenue} - \text{Expenses}")
    elif statement == "Balance Sheet":
        st.write("Assets, liabilities, and shareholders' equity at a point in time.")
        st.latex(r"\text{Assets} = \text{Liabilities} + \text{Equity}")
    else:
        st.write("Cash from operating, investing, and financing activities.")
        st.latex(r"\text{Net Cash Change} \approx \text{Operating} + \text{Investing} + \text{Financing}")
        st.caption("Exchange-rate effects and other reconciling items may apply.")


@st.cache_data(show_spinner=False)
def parse_pdf(pdf_bytes):
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        if document.needs_pass:
            raise ValueError("This PDF is password-protected.")
        return [page.get_text("text") for page in document]


@st.cache_data(show_spinner=False)
def parse_sections(pages_tuple):
    return find_filing_sections(list(pages_tuple))


@st.cache_data(show_spinner=False)
def parse_metrics(pages_tuple):
    return extract_financial_metrics(list(pages_tuple))


st.title("📊 Financial Statement AI Analyzer")
st.write("Explore SEC filings, examine financial trends, and trace results to their source pages.")
st.caption("Educational research tool — not investment advice. Automated extraction may be incorrect. Verify all figures, years, and units against the original filing.")

uploaded_file = st.file_uploader("Upload a public-company 10-K or 10-Q (PDF)", type=["pdf"])
if uploaded_file is None:
    st.info("Upload a PDF to begin. For beta testing, use publicly available company filings only.")
    learning_guide()
    st.stop()

pdf_bytes = uploaded_file.getvalue()
if not pdf_bytes:
    st.error("The uploaded file is empty.")
    st.stop()
if len(pdf_bytes) > 25 * 1024 * 1024:
    st.error("This MVP supports PDF files up to 25 MB.")
    st.stop()

fingerprint = hashlib.sha256(pdf_bytes).hexdigest()
if st.session_state.get("active_document") != fingerprint:
    # Never display charts generated from a previously uploaded company filing.
    for key in ("chart_data", "chart_units", "financial_data_editor"):
        st.session_state.pop(key, None)
    st.session_state["active_document"] = fingerprint

try:
    pages = parse_pdf(pdf_bytes)
except Exception as error:
    st.error(f"Unable to read this PDF: {error}")
    st.stop()

if not pages or not any(page.strip() for page in pages):
    st.error("No selectable text was found. This MVP does not support scanned/image-only PDFs.")
    st.stop()

try:
    sections = parse_sections(tuple(pages))
except Exception as error:
    sections = {}
    st.warning(f"Section navigation unavailable: {error}")
try:
    metrics_df = parse_metrics(tuple(pages))
except Exception as error:
    metrics_df = pd.DataFrame()
    st.warning(f"Metric extraction unavailable: {error}")

st.success(f"Loaded {uploaded_file.name} successfully.")
col1, col2, col3 = st.columns(3)
col1.metric("PDF pages", len(pages))
col2.metric("Filing sections", len(sections))
col3.metric("Metric candidates", len(metrics_df))

tab_overview, tab_sections, tab_metrics, tab_charts, tab_sources, tab_testing = st.tabs([
    "🏠 Overview", "📂 Filing Navigator", "💰 Financial Metrics",
    "📈 Visualizations", "📖 Sources & AI", "🧪 Testing & Launch"
])

with tab_overview:
    st.subheader("Document overview")
    st.write(f"**Characters extracted:** {len(''.join(pages)):,}")
    st.write(f"**Pages containing text:** {sum(bool(p.strip()) for p in pages)} / {len(pages)}")
    with st.expander("Extracted text preview"):
        st.text_area("First 5,000 characters", "\n".join(pages)[:5000], height=260)
    st.subheader("Financial statement learning guide")
    learning_guide()

with tab_sections:
    st.subheader("Filing Section Navigator")
    if not sections:
        st.warning("No supported filing sections were found. Try a different report.")
    else:
        selected = st.selectbox("Choose a section", list(sections), key="section_select")
        section = sections[selected]
        section_text = section["text"]
        st.caption(f"PDF pages {section['start_page']}–{section['end_page']}")
        st.text_area("Section text", section_text, height=450)
        with st.expander("Verify section boundaries"):
            st.write("**Beginning:**")
            st.code(section_text[:600], language=None)
            st.write("**End:**")
            st.code(section_text[-600:], language=None)

with tab_metrics:
    st.subheader("Financial metric candidates")
    st.warning("Candidates are NOT verified. PDF table extraction may select the wrong year, unit, or column.")
    if metrics_df.empty:
        st.info("No financial metric candidates were found in this document.")
    else:
        choices = ["All Metrics"] + sorted(metrics_df["Metric"].dropna().unique().tolist())
        metric_filter = st.selectbox("Filter metrics", choices)
        filtered = metrics_df if metric_filter == "All Metrics" else metrics_df[metrics_df["Metric"] == metric_filter]
        filtered = filtered.reset_index(drop=True)
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        chosen = st.selectbox("Inspect candidate", range(len(filtered)), format_func=lambda i: (
            f"{filtered.iloc[i]['Metric']} — PDF page {filtered.iloc[i]['PDF Page']} (row {i+1})"
        ))
        candidate = filtered.iloc[chosen]
        source_page = int(candidate["PDF Page"])
        st.write(f"**Candidate value:** {candidate['Candidate Value']}")
        st.write(f"**Source:** PDF page {source_page}")
        st.code(str(candidate["Source Text"]), language=None)
        with st.expander("Nearby extracted source text"):
            st.code(find_source_context(pages, source_page, candidate["Source Text"]), language=None)
        st.download_button("Download unverified candidates (CSV)", metrics_df.to_csv(index=False),
                           file_name="metric_candidates_unverified.csv", mime="text/csv")

with tab_charts:
    st.subheader("Financial visualizations")
    st.write("Enter values you have checked against the original PDF. Use consistent reporting periods and units.")
    units = st.selectbox("Units", ["USD millions", "USD thousands", "USD"], key="chart_unit_select")
    starter = pd.DataFrame({
        "Year": pd.Series([2024, 2025], dtype="int64"),
        "Revenue": pd.Series([None, None], dtype="float64"),
        "Net Income": pd.Series([None, None], dtype="float64"),
        "Source Page": pd.Series([None, None], dtype="float64"),
    })
    edited = st.data_editor(starter, num_rows="dynamic", hide_index=True,
                            use_container_width=True, key="financial_data_editor")
    st.caption("Years are placeholders. Replace them and enter figures from the uploaded report. Source Page refers to the PDF page number, not the printed page number.")
    if st.button("Generate charts", type="primary"):
        try:
            clean = validate_chart_data(edited)
            if clean.empty:
                st.error("Enter at least one complete row.")
            elif (clean["Source Page"] > len(pages)).any():
                st.error("A source page is beyond the end of this PDF.")
            else:
                st.session_state["chart_data"] = clean
                st.session_state["chart_units"] = units
                st.success("Chart inputs passed format checks. Financial accuracy still requires manual verification.")
        except (ValueError, TypeError, KeyError) as error:
            st.error(f"Please correct the chart inputs: {error}")
    if "chart_data" in st.session_state:
        chart_data = st.session_state["chart_data"]
        chart_units = st.session_state["chart_units"]
        st.caption(f"Figures in {chart_units}. Entered values are user-supplied, not automatically verified.")
        latest = chart_data.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Latest revenue", f"{latest['Revenue']:,.2f}")
        c2.metric("Latest net income", f"{latest['Net Income']:,.2f}")
        c3.metric("Net profit margin", f"{latest['Profit Margin (%)']:.2f}%")
        graph_tabs = st.tabs(["Revenue", "Net income", "Comparison", "Profit margin"])
        makers = [
            lambda: create_revenue_chart(chart_data, chart_units),
            lambda: create_income_chart(chart_data, chart_units),
            lambda: create_comparison_chart(chart_data, chart_units),
            lambda: create_margin_chart(chart_data),
        ]
        for chart_tab, make_chart in zip(graph_tabs, makers):
            with chart_tab:
                try:
                    st.plotly_chart(make_chart(), use_container_width=True)
                except Exception as error:
                    st.error(f"Unable to render chart: {error}")
        st.dataframe(chart_data, use_container_width=True, hide_index=True)
        st.download_button("Download chart data (CSV)", chart_data.to_csv(index=False),
                           file_name="verified_chart_inputs.csv", mime="text/csv")

with tab_sources:
    st.subheader("PDF source viewer")
    page_number = st.number_input("PDF page number", min_value=1, max_value=len(pages), value=1, step=1)
    st.text_area(f"Extracted text — PDF page {page_number}", get_page_text(pages, page_number), height=400)
    st.caption("For complex tables, compare this extracted text with the visual PDF page. Text extraction may change column order.")
    st.subheader("AI preparation")
    st.write("Create a page-referenced text file for a future retrieval-based AI assistant.")
    cited_text = build_cited_document(pages)
    with st.expander("Preview page-referenced text"):
        st.code(cited_text[:3500], language=None)
    st.download_button("Download page-referenced text", cited_text,
                       file_name="page_referenced_filing.txt", mime="text/plain")
    st.info("This feature prepares source text; it does not yet answer questions with AI or verify AI citations.")

with tab_testing:
    st.subheader("Document validation")
    try:
        checks = validate_document(pages, sections, metrics_df)
        st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)
        passed = sum(check.get("Status") == "PASS" for check in checks)
        st.metric("Basic checks passed", f"{passed}/{len(checks)}")
    except Exception as error:
        st.error(f"Validation checks failed: {error}")
    st.caption("A passing result does not prove that financial figures or citations are accurate.")
    st.subheader("Pre-launch checklist")
    st.checkbox("Tested Target's filing and checked section boundaries")
    st.checkbox("Tested a second company's filing")
    st.checkbox("Checked sample financial figures, units, and PDF pages manually")
    st.checkbox("Confirmed chart data resets after switching PDFs")
    st.checkbox("Reviewed privacy and hosting configuration")
    st.checkbox("Verified public deployment works in a fresh browser session")
    st.warning("Beta guidance: Upload public filings only. Do not upload confidential or personal financial documents. This app is for educational research, not investment recommendations.")
