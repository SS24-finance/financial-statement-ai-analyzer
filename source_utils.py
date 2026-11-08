
import re


def get_page_text(pages, page_number):
    """Return text from a 1-indexed PDF page."""

    if not 1 <= page_number <= len(pages):
        return ""

    return pages[page_number - 1]


def find_source_context(
    pages,
    page_number,
    source_text,
    context_lines=4
):
    """
    Find the original line on a PDF page
    and return nearby lines for verification.
    """

    page_text = get_page_text(
        pages,
        page_number
    )

    if not page_text:
        return "Page not found."

    lines = page_text.splitlines()

    target = " ".join(
        str(source_text).split()
    ).lower()

    for index, line in enumerate(lines):

        cleaned = " ".join(
            line.split()
        ).lower()

        if cleaned == target or (
            target and target in cleaned
        ):

            start = max(
                0,
                index - context_lines
            )

            end = min(
                len(lines),
                index + context_lines + 1
            )

            return "\n".join(
                lines[start:end]
            )

    return page_text[:2000]


def build_cited_document(pages):
    """
    Create a text document with PDF page
    references for future AI analysis.
    """

    chunks = []

    for page_number, text in enumerate(
        pages,
        start=1
    ):

        if not text.strip():
            continue

        chunks.append(
            f"[PDF PAGE {page_number}]\n"
            f"{text.strip()}\n"
            f"[/PDF PAGE {page_number}]"
        )

    return "\n\n".join(chunks)


def validate_document(pages, sections, metrics_df):
    """
    Run basic quality checks on extraction.
    """

    results = []

    def add_check(name, passed, details):
        results.append({
            "Check": name,
            "Status": (
                "PASS" if passed else "REVIEW"
            ),
            "Details": details
        })

    add_check(
        "PDF contains pages",
        len(pages) > 0,
        f"{len(pages)} pages detected"
    )

    pages_with_text = sum(
        bool(page.strip())
        for page in pages
    )

    add_check(
        "Text extraction",
        pages_with_text == len(pages),
        f"{pages_with_text} of "
        f"{len(pages)} pages contain text"
    )

    add_check(
        "Filing sections",
        len(sections) >= 4,
        f"{len(sections)} sections detected"
    )

    add_check(
        "Financial metrics",
        not metrics_df.empty,
        f"{len(metrics_df)} candidates found"
    )

    if not metrics_df.empty:

        valid_pages = metrics_df[
            "PDF Page"
        ].between(
            1,
            len(pages)
        ).all()

        add_check(
            "Metric source pages",
            bool(valid_pages),
            "Checks whether candidate page "
            "numbers exist in the PDF"
        )

        has_source_text = metrics_df[
            "Source Text"
        ].fillna("").str.strip().ne("").all()

        add_check(
            "Metric source text",
            bool(has_source_text),
            "Checks whether candidates "
            "have source text"
        )

    return results
