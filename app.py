
import streamlit as st
import fitz
import pandas as pd

from filing_parser import find_filing_sections
from financial_metrics import extract_financial_metrics

from source_utils import (
    get_page_text,
    find_source_context,
    build_cited_document,
    validate_document
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
    "explore financial data, business risks, "
    "and source-backed financial information."
)


# ---------------------------------------------------
# PDF UPLOAD
# ---------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a financial report",
    type=["pdf"]
)


if uploaded_file is not None:

    # -----------------------------------------------
    # PDF EXTRACTION
    # -----------------------------------------------

    try:

        pdf_bytes = uploaded_file.getvalue()

        if not pdf_bytes:
            st.error("The PDF is empty.")
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
            f"PDF extraction failed: {error}"
        )

        st.stop()

    st.success("PDF uploaded successfully!")

    # -----------------------------------------------
    # DOCUMENT OVERVIEW
    # -----------------------------------------------

    st.header("Document Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Pages",
            page_count
        )

    with col2:
        st.metric(
            "Characters Extracted",
            f"{len(full_text):,}"
        )

    with st.expander("View Extracted Text"):

        st.text_area(
            "PDF Text Preview",
            value=full_text[:5000],
            height=300
        )

    # -----------------------------------------------
    # FILING NAVIGATOR
    # -----------------------------------------------

    st.divider()

    st.header("📂 Filing Section Navigator")

    try:
        sections = find_filing_sections(pages)

    except Exception as error:

        st.error(
            f"Section detection failed: {error}"
        )

        sections = {}

    if sections:

        selected_section = st.selectbox(
            "Choose a filing section",
            list(sections.keys())
        )

        section_data = sections[selected_section]

        section_text = section_data["text"]

        start_page = section_data["start_page"]
        end_page = section_data["end_page"]

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Starting PDF Page",
                start_page
            )

        with col2:
            st.metric(
                "Ending PDF Page",
                end_page
            )

        st.text_area(
            "Section Content",
            value=section_text,
            height=400
        )

        with st.expander(
            "🔍 Verify Extracted Section"
        ):

            st.write(
                "**Beginning of section:**"
            )

            st.code(
                section_text[:600],
                language=None
            )

            st.write(
                "**End of section:**"
            )

            st.code(
                section_text[-600:],
                language=None
            )

    else:

        st.warning(
            "No filing sections were detected."
        )

    # -----------------------------------------------
    # FINANCIAL METRICS
    # -----------------------------------------------

    st.divider()

    st.header("💰 Financial Metrics Extraction")

    st.info(
        "Extracted values are candidates. "
        "Verify their reporting year, units, "
        "and source before using them."
    )

    try:

        metrics_df = extract_financial_metrics(
            pages
        )

    except Exception as error:

        st.error(
            f"Metric extraction failed: {error}"
        )

        metrics_df = pd.DataFrame()

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

        metric_options = [
            "All Metrics"
        ] + sorted(
            metrics_df["Metric"].unique()
        )

        selected_metric = st.selectbox(
            "Filter financial metrics",
            metric_options
        )

        if selected_metric == "All Metrics":

            filtered_df = metrics_df.copy()

        else:

            filtered_df = metrics_df[
                metrics_df["Metric"]
                == selected_metric
            ].copy()

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

        # -------------------------------------------
        # SOURCE VERIFICATION
        # -------------------------------------------

        st.subheader("Verify Financial Data")

        candidate_index = st.selectbox(
            "Choose a metric candidate",
            range(len(filtered_df)),
            format_func=lambda i: (
                f"{filtered_df.iloc[i]['Metric']} "
                f"— Page "
                f"{filtered_df.iloc[i]['PDF Page']}"
            )
        )

        candidate = filtered_df.iloc[
            candidate_index
        ]

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
            f"**Source:** PDF Page {source_page}"
        )

        st.write("**Original Source Line:**")

        st.code(
            str(candidate["Source Text"]),
            language=None
        )

        # -------------------------------------------
        # NEW: SOURCE CONTEXT
        # -------------------------------------------

        with st.expander(
            "📄 View Source Context"
        ):

            context = find_source_context(
                pages,
                source_page,
                candidate["Source Text"]
            )

            st.code(
                context,
                language=None
            )

            st.caption(
                "This context comes from the "
                "PDF's extracted text. Verify "
                "table alignment in the PDF."
            )

        csv_data = metrics_df.to_csv(
            index=False
        )

        st.download_button(
            "Download Financial Metrics CSV",
            data=csv_data,
            file_name="financial_metrics.csv",
            mime="text/csv"
        )

    else:

        st.warning(
            "No financial metrics were detected."
        )

    # -----------------------------------------------
    # NEW: PDF SOURCE VIEWER
    # -----------------------------------------------

    st.divider()

    st.header("📖 PDF Source Viewer")

    st.write(
        "Inspect the original extracted text "
        "from any PDF page."
    )

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
        height=400
    )

    # -----------------------------------------------
    # NEW: DOCUMENT VALIDATION
    # -----------------------------------------------

    st.divider()

    st.header("🧪 Document Validation")

    st.write(
        "Run automatic checks to identify "
        "potential extraction problems."
    )

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

    total = len(validation_results)

    st.metric(
        "Validation Checks Passed",
        f"{passed}/{total}"
    )

    st.caption(
        "Passing these checks does not "
        "guarantee financial accuracy. "
        "They test basic extraction quality."
    )

    # -----------------------------------------------
    # NEW: AI-READY DOCUMENT
    # -----------------------------------------------

    st.divider()

    st.header("🤖 AI-Ready Document")

    st.write(
        "Prepare extracted text with page "
        "references for future AI analysis."
    )

    cited_document = build_cited_document(
        pages
    )

    with st.expander(
        "Preview Page-Referenced Text"
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
        "The text includes PDF page markers. "
        "A future AI model can use these "
        "markers to generate source references, "
        "but citations will still need "
        "verification."
    )


# ---------------------------------------------------
# FINANCIAL STATEMENT LEARNING GUIDE
# ---------------------------------------------------

st.divider()

st.header("📚 Understanding Financial Statements")

statement = st.selectbox(
    "Choose a financial statement",
    [
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement"
    ]
)


if statement == "Income Statement":

    st.subheader("Income Statement")

    st.write(
        "Shows a company's revenue, "
        "expenses, and profitability "
        "over a reporting period."
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

    st.subheader("Balance Sheet")

    st.write(
        "Shows a company's assets, "
        "liabilities, and shareholders' "
        "equity at a specific date."
    )

    st.info(
        "Key metrics: Total Assets, "
        "Total Liabilities, Equity"
    )

    st.latex(
        r"\text{Assets} = "
        r"\text{Liabilities} + "
        r"\text{Equity}"
    )


elif statement == "Cash Flow Statement":

    st.subheader("Cash Flow Statement")

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
        "effects may also affect cash changes."
    )
