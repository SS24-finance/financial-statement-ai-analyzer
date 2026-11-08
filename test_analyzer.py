
import unittest

from financial_visualizations import (
    validate_chart_data
)

from source_utils import (
    get_page_text,
    find_source_context,
    build_cited_document,
)


class TestFinancialAnalyzer(unittest.TestCase):

    def setUp(self):
        self.sample_data = [
            {
                "Year": 2024,
                "Revenue": 100,
                "Net Income": 10,
                "Source Page": 12,
            },
            {
                "Year": 2025,
                "Revenue": 120,
                "Net Income": 12,
                "Source Page": 12,
            },
        ]

        self.sample_pages = [
            "Business overview",
            "Net sales 120 100\nNet income 12 10",
        ]

    def test_profit_margin(self):
        df = validate_chart_data(
            self.sample_data
        )

        self.assertAlmostEqual(
            df.iloc[0]["Profit Margin (%)"],
            10.0
        )

    def test_revenue_growth(self):
        df = validate_chart_data(
            self.sample_data
        )

        self.assertAlmostEqual(
            df.iloc[1]["Revenue Growth (%)"],
            20.0
        )

    def test_duplicate_years(self):
        duplicated = [
            self.sample_data[0],
            self.sample_data[0],
        ]

        with self.assertRaises(ValueError):
            validate_chart_data(duplicated)

    def test_source_page(self):
        self.assertEqual(
            get_page_text(self.sample_pages, 2),
            self.sample_pages[1]
        )

    def test_source_context(self):
        context = find_source_context(
            self.sample_pages,
            2,
            "Net sales 120 100"
        )

        self.assertIn(
            "Net sales",
            context
        )

    def test_ai_ready_pages(self):
        text = build_cited_document(
            self.sample_pages
        )

        self.assertIn(
            "[PDF PAGE 2]",
            text
        )


if __name__ == "__main__":
    unittest.main()
