from io import StringIO

import pandas as pd
import requests


KASE_SHARES_URL = (
    "https://kase.kz/en/markets/shares-and-adr-gdr"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/130 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# =========================================================
# HELPERS
# =========================================================

def _clean_column_name(column):
    """
    Convert table column names into a predictable format.
    """

    if isinstance(column, tuple):
        column = " ".join(
            str(part)
            for part in column
            if str(part) != "nan"
        )

    column = str(column)

    column = column.replace("\xa0", " ")
    column = " ".join(column.split())

    return column.strip()


def _parse_number(value):
    """
    Convert KASE-formatted numbers:
    35 645,00 -> 35645.00
    0,830     -> 0.830
    """

    if pd.isna(value):
        return None

    text = str(value).strip()

    if text in {"", "-", "–", "—"}:
        return None

    text = (
        text
        .replace("\xa0", "")
        .replace(" ", "")
        .replace("%", "")
        .replace(",", ".")
    )

    try:
        return float(text)

    except ValueError:
        return None


# =========================================================
# DOWNLOAD PAGE
# =========================================================

def _download_kase_page():
    """
    Download the official KASE share-market page.
    """

    response = requests.get(
        KASE_SHARES_URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    return response.text


# =========================================================
# FIND INSTRUMENT TABLE
# =========================================================

def _find_instruments_table(html):
    """
    Find the table containing:
    Ticker / Company / ISIN / Type / Currency.
    """

    tables = pd.read_html(
        StringIO(html)
    )

    for table in tables:

        table.columns = [
            _clean_column_name(column)
            for column in table.columns
        ]

        normalized_columns = {
            column.lower(): column
            for column in table.columns
        }

        required = {
            "ticker",
            "company",
            "isin",
            "type",
            "currency"
        }

        if required.issubset(
            normalized_columns.keys()
        ):
            return table

    return pd.DataFrame()


# =========================================================
# PUBLIC API
# =========================================================

def get_kase_instruments():
    """
    Download all share / ADR / GDR instruments
    currently exposed by KASE on its market page.
    """

    try:

        html = _download_kase_page()

        table = _find_instruments_table(
            html
        )

        if table.empty:
            return pd.DataFrame()

        rename_map = {}

        for column in table.columns:

            lower = column.lower()

            if lower == "ticker":
                rename_map[column] = "Ticker"

            elif lower == "company":
                rename_map[column] = "Company"

            elif lower == "isin":
                rename_map[column] = "ISIN"

            elif lower == "type":
                rename_map[column] = "Type"

            elif lower == "currency":
                rename_map[column] = "Currency"

            elif lower.startswith("price"):
                rename_map[column] = "Price"

            elif lower.startswith("volume"):
                rename_map[column] = "Volume"

            elif lower == "date":
                rename_map[column] = "Date"

            elif "liquidity" in lower:
                rename_map[column] = "Liquidity"

            elif "market-maker" in lower:
                rename_map[column] = "Market Maker"

        table = table.rename(
            columns=rename_map
        )

        # ---------------------------------------------
        # REMOVE EMPTY / DUPLICATE ROWS
        # ---------------------------------------------

        if "Ticker" not in table.columns:
            return pd.DataFrame()

        table["Ticker"] = (
            table["Ticker"]
            .astype(str)
            .str.strip()
        )

        table = table[
            table["Ticker"].notna()
        ]

        table = table[
            table["Ticker"] != ""
        ]

        table = table[
            table["Ticker"].str.lower()
            != "ticker"
        ]

        table = table.drop_duplicates(
            subset=["Ticker"],
            keep="first"
        )

        # ---------------------------------------------
        # CLEAN TEXT
        # ---------------------------------------------

        text_columns = [
            "Company",
            "ISIN",
            "Type",
            "Currency",
            "Date",
            "Liquidity",
            "Market Maker"
        ]

        for column in text_columns:

            if column in table.columns:

                table[column] = (
                    table[column]
                    .astype(str)
                    .str.replace(
                        "\xa0",
                        " ",
                        regex=False
                    )
                    .str.strip()
                )

        # ---------------------------------------------
        # CLEAN NUMBERS
        # ---------------------------------------------

        if "Price" in table.columns:

            table["Price"] = (
                table["Price"]
                .apply(_parse_number)
            )

        if "Volume" in table.columns:

            table["Volume"] = (
                table["Volume"]
                .apply(_parse_number)
            )

        # ---------------------------------------------
        # SOURCE
        # ---------------------------------------------

        table["Exchange"] = "KASE"

        table["Source"] = (
            "Kazakhstan Stock Exchange"
        )

        # Preferred column order

        preferred_columns = [
            "Ticker",
            "Company",
            "ISIN",
            "Type",
            "Currency",
            "Price",
            "Volume",
            "Date",
            "Liquidity",
            "Market Maker",
            "Exchange",
            "Source"
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column in table.columns
        ]

        return (
            table[available_columns]
            .reset_index(drop=True)
        )

    except (
        requests.RequestException,
        ValueError,
        ImportError
    ):

        return pd.DataFrame()


# =========================================================
# SEARCH
# =========================================================

def search_kase_instruments(
    query,
    instruments=None
):
    """
    Search by ticker, company name or ISIN.
    """

    if instruments is None:

        instruments = (
            get_kase_instruments()
        )

    if instruments.empty:
        return instruments

    if not query:
        return instruments

    query = str(query).strip().lower()

    mask = pd.Series(
        False,
        index=instruments.index
    )

    for column in [
        "Ticker",
        "Company",
        "ISIN"
    ]:

        if column in instruments.columns:

            mask |= (
                instruments[column]
                .astype(str)
                .str.lower()
                .str.contains(
                    query,
                    regex=False,
                    na=False
                )
            )

    return (
        instruments[mask]
        .reset_index(drop=True)
    )


# =========================================================
# ASSET RESOLVER
# =========================================================

def resolve_kase_asset(
    query,
    instruments=None
):
    """
    Resolve:
    Air Astana -> AIRA
    Halyk Bank -> HSBK
    AIRA       -> AIRA
    """

    if instruments is None:

        instruments = (
            get_kase_instruments()
        )

    if instruments.empty:
        return None

    query = str(query).strip().lower()

    # Exact ticker match

    ticker_match = instruments[
        instruments["Ticker"]
        .astype(str)
        .str.lower()
        == query
    ]

    if not ticker_match.empty:

        return (
            ticker_match
            .iloc[0]
            .to_dict()
        )

    # Exact company match

    if "Company" in instruments.columns:

        company_match = instruments[
            instruments["Company"]
            .astype(str)
            .str.lower()
            == query
        ]

        if not company_match.empty:

            return (
                company_match
                .iloc[0]
                .to_dict()
            )

    # Partial search

    results = search_kase_instruments(
        query,
        instruments
    )

    if results.empty:
        return None

    return results.iloc[0].to_dict()


# =========================================================
# PIE-CHART DISTRIBUTION DATA
# =========================================================

def get_kase_distribution(
    column="Type",
    instruments=None
):
    """
    Create grouped data suitable for pie charts.

    Examples:
    Type     -> ordinary / preferred / GDR
    Currency -> KZT / USD
    """

    if instruments is None:

        instruments = (
            get_kase_instruments()
        )

    if (
        instruments.empty
        or column not in instruments.columns
    ):

        return pd.DataFrame()

    distribution = (
        instruments[column]
        .fillna("Unknown")
        .value_counts()
        .rename_axis(column)
        .reset_index(name="Assets")
    )

    return distribution