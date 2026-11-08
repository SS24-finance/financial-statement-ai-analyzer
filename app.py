
import streamlit as st
import fitz
import pandas as pd

from filing_parser import find_filing_sections
from financial_metrics import extract_financial_metrics


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
    "Upload a company's 10-K or 10-Q to explore "
    "its financial performance, financial "
    "statements, business operations, and risks."
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
    # EXTRACT PDF TEXT
    # -----------------------------------------------

    try:
        pdf_bytes = uploaded_file.getvalue()

        if not pdf_bytes:
            st.error("The uploaded PDF is empty.")
            st.stop()

        with fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        ) as doc:

            page_count = len(doc)

            pages = [
                page.get_text("text")
                for page in doc
            ]

        full_text = "\n".join(pages)

    except Exception as error:
        st.error(
            f"Could not read the PDF: {error}"
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

    # -----------------------------------------------
    # EXTRACTED TEXT PREVIEW
    # -----------------------------------------------

    with st.expander("View Extracted Text Preview"):

        if full_text.strip():
            st.text_area(
                "Report content",
                value=full_text[:5000],
                height=300,
                key="full_text_preview"
            )

        else:
            st.warning(
                "No selectable text was found. "
                "The PDF may contain scanned pages."
            )

    # -----------------------------------------------
    # FILING SECTION NAVIGATOR
    # -----------------------------------------------

    st.divider()

    st.header("📂 Filing Section Navigator")

    st.write(
        "Explore important sections of the "
        "company's financial filing."
    )

    try:
        sections = find_filing_sections(pages)

    except Exception as error:
        st.error(
            f"Could not identify sections: {error}"
        )
        sections = {}

    if sections:

        selected_section = st.selectbox(
            "Select a section to explore",
            list(sections.keys()),
            key="filing_section"
        )

        section_data = sections[selected_section]

        section_text = section_data["text"]

        start_page = section_data["start_page"]
        end_page = section_data["end_page"]

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "PDF Page Range",
                f"{start_page}–{end_page}"
            )

        with col2:
            st.metric(
                "Section Characters",
                f"{len(section_text):,}"
            )

        st.subheader(selected_section)

        st.text_area(
            "Section Content",
            value=section_text,
            height=400,
            key="section_content"
        )

        # -------------------------------------------
        # PARSER VERIFICATION
        # -------------------------------------------

        with st.expander(
            "🔍 Verify Extracted Section"
        ):

            st.write(
                "Check that the extracted text "
                "belongs to the selected section."
            )

            st.markdown(
                "**Beginning of section:**"
            )

            st.code(
                section_text[:600],
                language=None
            )

            st.markdown(
                "**End of section:**"
            )

            st.code(
                section_text[-600:],
                language=None
            )

            st.write(
                f"**Starting PDF page:** {start_page}"
            )

            st.write(
                f"**Ending PDF page:** {end_page}"
            )

            st.info(
                "Verify that the section starts "
                "with the correct heading and ends "
                "before the next filing section."
            )

    else:
        st.warning(
            "No filing sections were detected."
        )

    # -----------------------------------------------
    # FINANCIAL METRICS EXTRACTION
    # DAY 3 FEATURE
    # -----------------------------------------------

    st.divider()

    st.header("💰 Financial Metrics Extraction")

    st.write(
        "Automatically search the uploaded report "
        "for important financial metrics."
    )

    st.info(
        "These are candidate values, not verified "
        "financial results. Check the source PDF "
        "before using them in calculations."
    )

    try:
        metrics_df = extract_financial_metrics(
            pages
        )

    except Exception as error:
        st.error(
            f"Could not extract financial metrics: "
            f"{error}"
        )
        metrics_df = pd.DataFrame()

    if not metrics_df.empty:

        # -------------------------------------------
        # METRICS SUMMARY
        # -------------------------------------------

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

        # -------------------------------------------
        # METRIC FILTER
        # -------------------------------------------

        metric_options = [
            "All Metrics"
        ] + sorted(
            metrics_df["Metric"].unique()
        )

        selected_metric = st.selectbox(
            "Filter by financial metric",
            metric_options,
            key="metric_filter"
        )

        if selected_metric == "All Metrics":
            filtered_df = metrics_df.copy()

        else:
            filtered_df = metrics_df[
                metrics_df["Metric"] == selected_metric
            ].copy()

        # -------------------------------------------
        # FINANCIAL METRICS TABLE
        # -------------------------------------------

        st.subheader("Extracted Financial Data")

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

        # -------------------------------------------
        # SOURCE VERIFICATION
        # -------------------------------------------

        st.subheader("Verify a Financial Metric")

        selected_row = st.selectbox(
            "Select a candidate to inspect",
            range(len(filtered_df)),
            format_func=lambda i: (
                f"{filtered_df.iloc[i]['Metric']} "
                f"— PDF Page "
                f"{filtered_df.iloc[i]['PDF Page']}"
            ),
            key="verify_metric"
        )

        candidate = filtered_df.iloc[selected_row]

        st.write(
            f"**Metric:** {candidate['Metric']}"
        )

        st.write(
            f"**Candidate Value:** "
            f"{candidate['Candidate Value']:,.2f}"
        )

        st.write(
            f"**PDF Page:** "
            f"{candidate['PDF Page']}"
        )

        st.write("**Original Extracted Line:**")

        st.code(
            candidate["Source Text"],
            language=None
        )

        st.warning(
            "Check the reporting year, units, "
            "and column alignment in the PDF. "
            "A number appearing beside a label "
            "is not automatically the correct "
            "current-year value."
        )

        # -------------------------------------------
        # DOWNLOAD EXTRACTED DATA
        # -------------------------------------------

        csv_data = metrics_df.to_csv(
            index=False
        )

        st.download_button(
            label="Download Financial Metrics CSV",
            data=csv_data,
            file_name="financial_metrics.csv",
            mime="text/csv"
        )

    else:
        st.warning(
            "No financial metric candidates "
            "were found. The report may use "
            "a different table format."
        )


# ---------------------------------------------------
# FINANCIAL STATEMENT LEARNING GUIDE
# ---------------------------------------------------

st.divider()

st.header("📚 Understanding Financial Statements")

st.write(
    "Learn about the three main financial "
    "statements found in company filings."
)

statement = st.selectbox(
    "Choose a financial statement",
    [
        "Income Statement",
        "Balance Sheet",
        "Cash Flow Statement"
    ],
    key="learning_guide"
)


# ---------------------------------------------------
# INCOME STATEMENT
# ---------------------------------------------------

if statement == "Income Statement":

    st.subheader("Income Statement")

    st.write(
        "The income statement shows revenue, "
        "expenses, and profit over a reporting "
        "period."
    )

    st.info(
        "Key metrics: Revenue, Operating Income, "
        "Net Income, Earnings Per Share"
    )

    st.latex(
        r"\text{Net Income} = "
        r"\text{Revenue} - \text{Expenses}"
    )


# ---------------------------------------------------
# BALANCE SHEET
# ---------------------------------------------------

elif statement == "Balance Sheet":

    st.subheader("Balance Sheet")

    st.write(
        "The balance sheet shows what a company "
        "owns, what it owes, and shareholders' "
        "equity at a specific point in time."
    )

    st.info(
        "Key metrics: Assets, Liabilities, "
        "Shareholders' Equity"
    )

    st.latex(
        r"\text{Assets} = "
        r"\text{Liabilities} + "
        r"\text{Equity}"
    )


# ---------------------------------------------------
# CASH FLOW STATEMENT
# ---------------------------------------------------

elif statement == "Cash Flow Statement":

    st.subheader("Cash Flow Statement")

    st.write(
        "The cash flow statement shows how "
        "cash enters and leaves a company "
        "through operating, investing, "
        "and financing activities."
    )

    st.info(
        "Key categories: Operating Activities, "
        "Investing Activities, "
        "Financing Activities"
    )

    st.latex(
        r"\text{Net Change in Cash} = "
        r"\text{Operating Cash Flow} + "
        r"\text{Investing Cash Flow} + "
        r"\text{Financing Cash Flow}"
    )

    st.caption(
        "Simplified formula; reported changes "
        "may also include exchange-rate effects."
    )
