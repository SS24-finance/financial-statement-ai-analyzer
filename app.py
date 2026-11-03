
import streamlit as st
import fitz

st.set_page_config(
    page_title="Financial Statement AI Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("Financial Statement AI Analyzer")
st.write(
    "Upload a company's 10-K or 10-Q to begin "
    "analyzing its financial performance."
)

uploaded_file = st.file_uploader(
    "Upload a financial report",
    type=["pdf"]
)

if uploaded_file is not None:
    try:
        pdf_bytes = uploaded_file.getvalue()

        if not pdf_bytes:
            st.error("The uploaded file is empty.")
            st.stop()

        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            page_count = len(doc)
            pages = [
                page.get_text("text")
                for page in doc
            ]

        full_text = "\n".join(pages)

        st.success("PDF uploaded successfully!")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Pages", page_count)

        with col2:
            st.metric("Characters Extracted", len(full_text))

        st.subheader("Extracted Text Preview")

        if full_text.strip():
            st.text_area(
                "Report content",
                value=full_text[:5000],
                height=350
            )
        else:
            st.warning(
                "No selectable text was found. "
                "This PDF may contain scanned pages."
            )

    except Exception as error:
        st.error(f"Could not read the PDF: {error}")

# ---------------------------------------------------
# Financial Statement Learning Guide
# ---------------------------------------------------

st.divider()

st.header("Understanding Financial Statements")

st.write(
    "Learn about the three core financial "
    "statements found in a company's 10-K."
)

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
        "Shows revenue, expenses, and profit "
        "over a reporting period."
    )

    st.info(
        "Key metrics: Revenue, Operating Income, "
        "Net Income, Earnings Per Share"
    )

elif statement == "Balance Sheet":
    st.subheader("Balance Sheet")

    st.write(
        "Shows what a company owns and owes "
        "at a specific point in time."
    )

    st.info(
        "Key metrics: Assets, Liabilities, "
        "Shareholders' Equity"
    )

    st.latex(
        r"Assets = Liabilities + Equity"
    )

elif statement == "Cash Flow Statement":
    st.subheader("Cash Flow Statement")

    st.write(
        "Shows cash generated and spent "
        "through business activities."
    )

    st.info(
        "Key categories: Operating, Investing, "
        "Financing Activities"
    )
