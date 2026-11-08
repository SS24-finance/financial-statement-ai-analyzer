
import re
import pandas as pd


# ---------------------------------------------------
# FINANCIAL METRICS TO SEARCH FOR
# ---------------------------------------------------

METRIC_PATTERNS = {
    "Net Sales": [
        r"^(?:net\s+sales|total\s+net\s+sales)\b",
    ],
    "Net Income": [
        r"^(?:net\s+income|net\s+earnings)\b",
    ],
    "Total Assets": [
        r"^total\s+assets\b",
    ],
    "Total Liabilities": [
        r"^total\s+liabilities\b",
    ],
    "Operating Cash Flow": [
        r"^net\s+cash\s+(?:provided\s+by|from)"
        r"\s+operating\s+activities\b",
        r"^cash\s+provided\s+by\s+operating"
        r"\s+activities\b",
    ],
}


# ---------------------------------------------------
# CLEAN FINANCIAL NUMBERS
# ---------------------------------------------------

def parse_number(value):
    """
    Convert financial text into a Python number.

    Examples:
    '104,780' -> 104780
    '(2,500)' -> -2500
    '$59,490' -> 59490
    """

    value = value.strip()

    negative = (
        value.startswith("(")
        and value.endswith(")")
    )

    value = value.replace("$", "")
    value = value.replace(",", "")
    value = value.replace("(", "")
    value = value.replace(")", "")

    try:
        number = float(value)

        if negative:
            number = -number

        return number

    except ValueError:
        return None


# ---------------------------------------------------
# EXTRACT NUMBERS FROM A LINE
# ---------------------------------------------------

def get_numbers(text):
    """
    Find financial numbers, including numbers
    with commas and parentheses.
    """

    pattern = (
        r"(?<![\w.])"
        r"\(?-?\$?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?"
        r"|(?<![\w.])\(?-?\$?\d+(?:\.\d+)?\)?"
    )

    matches = re.findall(pattern, text)

    numbers = []

    for match in matches:
        number = parse_number(match)

        if number is not None:
            numbers.append(number)

    return numbers


# ---------------------------------------------------
# DETECT METRIC LABELS
# ---------------------------------------------------

def identify_metric(line):

    cleaned = " ".join(line.strip().split())

    for metric, patterns in METRIC_PATTERNS.items():

        for pattern in patterns:

            match = re.search(
                pattern,
                cleaned,
                flags=re.IGNORECASE
            )

            if match:
                return metric, cleaned[match.end():]

    return None, None


# ---------------------------------------------------
# FIND FINANCIAL METRIC CANDIDATES
# ---------------------------------------------------

def extract_financial_metrics(pages):
    """
    Search PDF pages for financial metric labels.

    Returns candidate values with source pages.

    IMPORTANT:
    The first number is not guaranteed to be
    the latest reporting year's value.
    """

    results = []

    for page_number, page_text in enumerate(
        pages,
        start=1
    ):

        lines = page_text.splitlines()

        for line_index, line in enumerate(lines):

            metric, remainder = identify_metric(line)

            if metric is None:
                continue

            # Start with the numbers on the same line
            numbers = get_numbers(remainder)

            # Some PDF tables put values below labels.
            # Search the next three lines as a fallback.
            if not numbers:

                for next_line in lines[
                    line_index + 1:line_index + 4
                ]:

                    # Stop if another named metric begins
                    next_metric, _ = identify_metric(
                        next_line
                    )

                    if next_metric is not None:
                        break

                    found = get_numbers(next_line)

                    if found:
                        numbers = found
                        break

            if not numbers:
                continue

            results.append({
                "Metric": metric,
                "Candidate Value": numbers[0],
                "Other Values": ", ".join(
                    f"{n:,.2f}" for n in numbers[1:]
                ),
                "PDF Page": page_number,
                "Source Text": line.strip(),
                "Status": "Needs verification",
            })

    columns = [
        "Metric",
        "Candidate Value",
        "Other Values",
        "PDF Page",
        "Source Text",
        "Status",
    ]

    return pd.DataFrame(
        results,
        columns=columns
    )
