
import streamlit as st
import fitz
import pandas as pd

from filing_parser import find_filing_sections
from financial_metrics import extract_financial_metrics

from source_utils import (
    get_page_text,
    find_source_context,
    build_cited_document,
    validate_document,
)

from financial_visualizations import (
    validate_chart_data,
    create_revenue_chart,
    create_income_chart,
    create_comparison_chart,
    create_margin_chart,
)


# ---------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------

st.set_page_config(
    page_title="Financial Statement AI Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Financial Statement AI Analyzer")

st.write(
    "Upload a company's 10-K or 10-Q to "
    "explore its financial performance, "
    "financial statements, and risks."
)


# ---------------------------------------------------
# FINANCIAL STATEMENT LEARNING GUIDE
# ---------------------------------------------------

def show_learning_guide():

    st.divider()
    st.header("📚 Financial Statement Learning Guide")

    statement = st.selectbox(
        "Choose a financial statement",
        [
            "Income Statement",
            "Balance Sheet",
            "Cash Flow Statement",
        ],
        key="learning_guide"
    )

    if statement == "Income Statement":

        st.write(
            "Shows revenue, expenses, and "
            "profit over a reporting period."
        )

        st.info(
            "Key metrics: Revenue, Operating "
            "Income, Net Income, EPS"
        )

        st.latex(
            r"\text{Net Income} = "
            r"\text{Revenue} - \text{Expenses}"
        )

    elif statement == "Balance Sheet":

        st.write(
            "Shows assets, liabilities, and "
            "shareholders' equity at a "
            "specific point in time."
        )

        st.info(
            "Key metrics: Total Assets, "
            "Total Liabilities, Equity"
        )

        st.latex(
            r"\text{Assets} = "
            r"\text{Liabilities} + \text{Equity}"
        )

    else:

        st.write(
            "Shows cash generated and spent "
            "through operating, investing, "
            "and financing activities."
        )

        st.info(
            "Key categories: Operating, "
            "Investing, Financing"
        )

        st.latex(
            r"\text{Net Change in Cash} = "
            r"\text{Operating} + "
            r"\text{Investing} + "
            r"\text{Financing}"
        )

        st.caption(
            "Simplified formula. Exchange-rate "
            "effects may also apply."
        )


# ---------------------------------------------------
# PDF UPLOAD
# ---------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a financial report",
    type=["pdf"]
)

if uploaded_file is None:

    st.info(
        "Upload a PDF to begin analyzing "
        "financial information."
    )

    show_learning_guide()
    st.stop()


# ---------------------------------------------------
# EXTRACT PDF TEXT
# ---------------------------------------------------

try:

    pdf_bytes = uploaded_file.getvalue()

    if not pdf_bytes:
        st.error("The uploaded PDF is empty.")
        st.stop()

    with fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    ) as doc:

        pages = [
            page.get_text("text")
            for page in doc
        ]

    page_count = len(pages)
    full_text = "\n".join(pages)

except Exception as error:

    st.error(
        f"Could not read the PDF: {error}"
    )
    st.stop()


st.success("PDF uploaded successfully!")


# ---------------------------------------------------
# EXTRACT SECTIONS AND METRICS
# ---------------------------------------------------

try:
    sections = find_filing_sections(pages)

except Exception as error:
    st.warning(
        f"Section detection issue: {error}"
    )
    sections = {}


try:
    metrics_df = extract_financial_metrics(pages)

except Exception as error:
    st.warning(
        f"Metric extraction issue: {error}"
    )
    metrics_df = pd.DataFrame()


# ---------------------------------------------------
# DOCUMENT OVERVIEW
# ---------------------------------------------------

st.header("Document Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("PDF Pages", page_count)

with col2:
    st.metric(
        "Characters Extracted",
        f"{len(full_text):,}"
    )

with col3:
    st.metric(
        "Filing Sections",
        len(sections)
    )

with st.expander("View Extracted Text Preview"):

    st.text_area(
        "Extracted text",
        value=full_text[:5000],
        height=300
    )


# ---------------------------------------------------
# FILING SECTION NAVIGATOR
# ---------------------------------------------------

st.divider()
st.header("📂 Filing Section Navigator")

if sections:

    selected_section = st.selectbox(
        "Select a filing section",
        list(sections.keys())
    )

    section_data = sections[selected_section]
    section_text = section_data["text"]

    start_page = section_data["start_page"]
    end_page = section_data["end_page"]

    st.write(
        f"**PDF Pages:** {start_page}–{end_page}"
    )

    st.text_area(
        "Section Content",
        value=section_text,
        height=400
    )

    with st.expander("🔍 Verify Extracted Section"):

        st.write("**Beginning:**")

        st.code(
            section_text[:600],
            language=None
        )

        st.write("**Ending:**")

        st.code(
            section_text[-600:],
            language=None
        )

else:
    st.warning("No filing sections detected.")


# ---------------------------------------------------
# FINANCIAL METRICS EXTRACTION
# ---------------------------------------------------

st.divider()
st.header("💰 Financial Metrics Extraction")

st.info(
    "These values are unverified candidates. "
    "Check the reporting year, units, and "
    "original financial statement."
)

if not metrics_df.empty:

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Candidates Found",
            len(metrics_df)
        )

    with col2:
        st.metric(
            "Unique Metrics",
            metrics_df["Metric"].nunique()
        )

    options = ["All Metrics"] + sorted(
        metrics_df["Metric"].unique()
    )

    selected_metric = st.selectbox(
        "Filter financial metrics",
        options
    )

    if selected_metric == "All Metrics":
        filtered_df = metrics_df.copy()

    else:
        filtered_df = metrics_df[
            metrics_df["Metric"] == selected_metric
        ].copy()

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Verify a Metric Candidate")

    candidate_index = st.selectbox(
        "Choose a candidate",
        range(len(filtered_df)),
        format_func=lambda i: (
            f"{filtered_df.iloc[i]['Metric']} "
            f"— PDF Page "
            f"{filtered_df.iloc[i]['PDF Page']}"
        )
    )

    candidate = filtered_df.iloc[candidate_index]

    source_page = int(
        candidate["PDF Page"]
    )

    st.write(
        f"**Metric:** {candidate['Metric']}"
    )

    st.write(
        f"**Candidate Value:** "
        f"{candidate['Candidate Value']:,.2f}"
    )

    st.write(
        f"**PDF Page:** {source_page}"
    )

    st.code(
        str(candidate["Source Text"]),
        language=None
    )

    with st.expander("📄 Source Context"):

        context = find_source_context(
            pages,
            source_page,
            candidate["Source Text"]
        )

        st.code(
            context,
            language=None
        )

    st.download_button(
        "Download Financial Metrics CSV",
        data=metrics_df.to_csv(index=False),
        file_name="financial_metrics.csv",
        mime="text/csv"
    )

else:
    st.warning(
        "No financial metric candidates found."
    )


# ---------------------------------------------------
# FINANCIAL VISUALIZATIONS
# ---------------------------------------------------

st.divider()
st.header("📈 Financial Visualizations")

st.write(
    "Enter financial figures verified against "
    "the uploaded report. Use the same units "
    "and reporting basis for every year."
)

st.warning(
    "Do not copy unverified extraction "
    "candidates directly into the charts."
)

units = st.selectbox(
    "Financial data units",
    [
        "USD millions",
        "USD thousands",
        "USD",
    ]
)

st.write(
    "Enter revenue, net income, fiscal year, "
    "and the PDF page supporting the figures."
)

if "verified_financial_data" not in st.session_state:

    st.session_state[
        "verified_financial_data"
    ] = pd.DataFrame({
        "Year": [2024, 2025],
        "Revenue": [None, None],
        "Net Income": [None, None],
        "Source Page": [None, None],
    })


edited_data = st.data_editor(
    st.session_state["verified_financial_data"],
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="financial_data_editor"
)

st.caption(
    "The starting years are placeholders. "
    "Replace them with the fiscal years "
    "shown in your report. Add or remove "
    "rows as needed."
)

if st.button("Generate Financial Charts"):

    try:

        chart_df = validate_chart_data(
            edited_data
        )

        if chart_df.empty:
            st.error(
                "Enter at least one year of data."
            )

        elif (
            chart_df["Source Page"] > page_count
        ).any():
            st.error(
                "A source page exceeds the "
                "uploaded PDF's page count."
            )

        else:

            st.session_state["chart_data"] = (
                chart_df
            )

            st.session_state["chart_units"] = units

            st.success(
                "Financial data validated!"
            )

    except ValueError as error:

        st.error(str(error))


if "chart_data" in st.session_state:

    chart_df = st.session_state["chart_data"]
    chart_units = st.session_state["chart_units"]

    st.subheader("Financial Performance Summary")

    latest = chart_df.iloc[-1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Latest Revenue",
            f"{latest['Revenue']:,.2f}"
        )

    with col2:
        st.metric(
            "Latest Net Income",
            f"{latest['Net Income']:,.2f}"
        )

    with col3:
        st.metric(
            "Net Profit Margin",
            f"{latest['Profit Margin (%)']:.2f}%"
        )

    st.caption(
        f"Financial values shown in {chart_units}."
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Revenue",
        "Net Income",
        "Comparison",
        "Profit Margin",
    ])

    with tab1:

        st.plotly_chart(
            create_revenue_chart(
                chart_df,
                chart_units
            ),
            use_container_width=True
        )

    with tab2:

        st.plotly_chart(
            create_income_chart(
                chart_df,
                chart_units
            ),
            use_container_width=True
        )

    with tab3:

        st.plotly_chart(
            create_comparison_chart(
                chart_df,
                chart_units
            ),
            use_container_width=True
        )

    with tab4:

        st.plotly_chart(
            create_margin_chart(chart_df),
            use_container_width=True
        )

    st.subheader("Verified Financial Data")

    st.dataframe(
        chart_df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download Chart Data CSV",
        data=chart_df.to_csv(index=False),
        file_name="verified_financial_data.csv",
        mime="text/csv"
    )


# ---------------------------------------------------
# PDF SOURCE VIEWER
# ---------------------------------------------------

st.divider()
st.header("📖 PDF Source Viewer")

selected_page = st.number_input(
    "Select PDF page",
    min_value=1,
    max_value=max(1, page_count),
    value=1,
    step=1
)

page_text = get_page_text(
    pages,
    selected_page
)

st.text_area(
    f"PDF Page {selected_page}",
    value=page_text,
    height=350
)


# ---------------------------------------------------
# DOCUMENT VALIDATION
# ---------------------------------------------------

st.divider()
st.header("🧪 Document Validation")

validation_results = validate_document(
    pages,
    sections,
    metrics_df
)

validation_df = pd.DataFrame(
    validation_results
)

st.dataframe(
    validation_df,
    use_container_width=True,
    hide_index=True
)

passed = sum(
    result["Status"] == "PASS"
    for result in validation_results
)

st.metric(
    "Validation Checks Passed",
    f"{passed}/{len(validation_results)}"
)

st.caption(
    "These checks identify potential "
    "extraction problems. They do not "
    "guarantee that financial values "
    "are accurate."
)


# ---------------------------------------------------
# AI-READY DOCUMENT
# ---------------------------------------------------

st.divider()
st.header("🤖 AI Preparation")

st.write(
    "Prepare financial filing text with "
    "PDF page references for future "
    "AI-powered analysis."
)

cited_document = build_cited_document(
    pages
)

with st.expander(
    "Preview AI-Ready Document"
):

    st.code(
        cited_document[:4000],
        language=None
    )

st.download_button(
    "Download AI-Ready Text",
    data=cited_document,
    file_name="page_referenced_filing.txt",
    mime="text/plain"
)

st.info(
    "The document includes page markers "
    "that a future AI system can use "
    "when generating source references. "
    "Any AI-generated citations must "
    "still be checked against the PDF."
)


# ---------------------------------------------------
# LEARNING GUIDE
# ---------------------------------------------------

show_learning_guide()
