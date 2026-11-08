
import re

# Sections we want to find in a 10-K
SECTIONS = {
    "Item 1 - Business": "1",
    "Item 1A - Risk Factors": "1A",
    "Item 7 - Management Discussion (MD&A)": "7",
    "Item 8 - Financial Statements": "8",
}

# All standard item numbers, used to find section endings
ITEM_NUMBERS = (
    "1A|1B|1C|1D|1|2|3|4|5|6|"
    "7A|7|8|9A|9B|9C|9|10|11|12|"
    "13|14|15|16"
)

HEADING_PATTERN = re.compile(
    rf"(?im)^[ \t]*item[ \t]+"
    rf"({ITEM_NUMBERS})[ \t]*[.:\-]?[ \t]+"
    rf"([^\n]{{3,150}})$"
)


def find_filing_sections(pages):
    """
    Find likely 10-K sections using item headings.

    pages: list of text strings, one per PDF page
    """
    matches = []

    for page_index, page_text in enumerate(pages):
        for match in HEADING_PATTERN.finditer(page_text):
            item_number = match.group(1).upper()
            heading = match.group(2).strip()

            matches.append({
                "item": item_number,
                "heading": heading,
                "page_index": page_index,
                "start": match.start(),
            })

    results = {}

    for label, item_number in SECTIONS.items():
        candidates = [
            m for m in matches
            if m["item"] == item_number
        ]

        # Ignore likely table-of-contents entries
        candidates = [
            m for m in candidates
            if not re.search(
                r"\.{3,}\s*\d+$",
                m["heading"]
            )
            and not re.search(
                r"\s{2,}\d{1,3}$",
                m["heading"]
            )
        ]

        if not candidates:
            continue

        # Prefer the later heading when the first
        # occurrence is in the table of contents.
        start_match = candidates[0]

        if (
            len(candidates) > 1
            and candidates[0]["page_index"] < 5
        ):
            start_match = candidates[1]

        start_page = start_match["page_index"]

        # Find the next item heading
        later_matches = [
            m for m in matches
            if (
                m["page_index"] > start_page
                or (
                    m["page_index"] == start_page
                    and m["start"] > start_match["start"]
                )
            )
        ]

        if later_matches:
            end_page = later_matches[0]["page_index"]
            end_offset = later_matches[0]["start"]
        else:
            end_page = len(pages) - 1
            end_offset = len(pages[end_page])

        if start_page == end_page:
            section_text = pages[start_page][
                start_match["start"]:end_offset
            ]
        else:
            chunks = [
                pages[start_page][start_match["start"]:]
            ]

            chunks.extend(
                pages[start_page + 1:end_page]
            )

            chunks.append(
                pages[end_page][:end_offset]
            )

            section_text = "\n".join(chunks)

        if len(section_text.strip()) < 200:
            continue

        results[label] = {
            "text": section_text,
            "start_page": start_page + 1,
            "end_page": end_page + 1,
        }

    return results
