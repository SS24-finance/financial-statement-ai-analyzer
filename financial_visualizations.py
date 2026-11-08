
import pandas as pd
import plotly.express as px


REQUIRED_COLUMNS = [
    "Year",
    "Revenue",
    "Net Income",
    "Source Page",
]


def validate_chart_data(data):
    """
    Validate user-entered financial data.
    Returns a cleaned DataFrame.
    """

    df = pd.DataFrame(data).copy()

    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {', '.join(missing)}"
        )

    if df.empty:
        return df

    for column in [
        "Year",
        "Revenue",
        "Net Income",
        "Source Page",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    if df[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError(
            "Every row needs a valid year, revenue, "
            "net income, and source page."
        )

    if df["Year"].duplicated().any():
        raise ValueError(
            "Each reporting year must appear once."
        )

    if (df["Revenue"] <= 0).any():
        raise ValueError(
            "Revenue must be greater than zero."
        )

    if (df["Source Page"] < 1).any():
        raise ValueError(
            "Source pages must be positive."
        )

    if (
        (df["Year"] % 1 != 0).any()
        or (df["Source Page"] % 1 != 0).any()
    ):
        raise ValueError(
            "Years and PDF page numbers must "
            "be whole numbers."
        )

    df["Year"] = df["Year"].astype(int)
    df["Source Page"] = df[
        "Source Page"
    ].astype(int)

    df = df.sort_values("Year")

    df["Profit Margin (%)"] = (
        df["Net Income"]
        / df["Revenue"]
        * 100
    )

    df["Revenue Growth (%)"] = (
        df["Revenue"].pct_change() * 100
    )

    return df.reset_index(drop=True)


def create_revenue_chart(df, units):
    fig = px.bar(
        df,
        x="Year",
        y="Revenue",
        title="Revenue by Year",
        labels={
            "Revenue": f"Revenue ({units})",
            "Year": "Fiscal Year",
        },
        hover_data=["Source Page"],
    )

    fig.update_xaxes(
        type="category"
    )

    return fig


def create_income_chart(df, units):
    fig = px.line(
        df,
        x="Year",
        y="Net Income",
        markers=True,
        title="Net Income Trend",
        labels={
            "Net Income": f"Net Income ({units})",
            "Year": "Fiscal Year",
        },
        hover_data=["Source Page"],
    )

    fig.update_xaxes(
        type="category"
    )

    return fig


def create_comparison_chart(df, units):
    comparison = df.melt(
        id_vars=["Year"],
        value_vars=[
            "Revenue",
            "Net Income",
        ],
        var_name="Metric",
        value_name="Value",
    )

    fig = px.bar(
        comparison,
        x="Year",
        y="Value",
        color="Metric",
        barmode="group",
        title="Revenue vs. Net Income",
        labels={
            "Value": f"Value ({units})",
            "Year": "Fiscal Year",
        },
    )

    fig.update_xaxes(
        type="category"
    )

    return fig


def create_margin_chart(df):
    fig = px.line(
        df,
        x="Year",
        y="Profit Margin (%)",
        markers=True,
        title="Net Profit Margin Trend",
        labels={
            "Year": "Fiscal Year",
            "Profit Margin (%)": "Net Profit Margin (%)",
        },
    )

    fig.update_xaxes(
        type="category"
    )

    return fig
