import pandas as pd


# =========================================================
# KAZAKHSTAN MARKET CATALOG
# =========================================================

KZ_ASSETS = {
    "AIRA": {
        "name": "Air Astana",
        "sector": "Airlines",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ1C00004050",
    },

    "CCBN": {
        "name": "Bank CenterCredit",
        "sector": "Banking",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ0007786572",
    },

    "HSBK": {
        "name": "Halyk Bank",
        "sector": "Banking",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ000A0LE0S4",
    },

    "KSPI": {
        "name": "Kaspi.kz",
        "sector": "Fintech",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ1C00001536",
    },

    "KZAP": {
        "name": "Kazatomprom",
        "sector": "Uranium",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ1C00001619",
    },

    "KMGZ": {
        "name": "KazMunayGas",
        "sector": "Oil & Gas",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ1C00001122",
    },

    "KEGC": {
        "name": "KEGOC",
        "sector": "Utilities",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ1C00000959",
    },

    "KCEL": {
        "name": "Kcell",
        "sector": "Telecommunications",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ1C00000876",
    },

    "KZTK": {
        "name": "Kazakhtelecom",
        "sector": "Telecommunications",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ0009093241",
    },

    "KZTO": {
        "name": "KazTransOil",
        "sector": "Oil Transportation",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ1C00000744",
    },

    "ASBN": {
        "name": "ForteBank",
        "sector": "Banking",
        "exchange": "KASE",
        "currency": "KZT",
        "isin": "KZ000A0F4546",
    },
}


# =========================================================
# DATAFRAME
# =========================================================

def get_kz_asset_catalog():
    """
    Return Kazakhstan securities catalog.
    """

    rows = []

    for ticker, asset in KZ_ASSETS.items():

        rows.append({
            "Ticker": ticker,
            "Company": asset["name"],
            "Sector": asset["sector"],
            "Exchange": asset["exchange"],
            "Currency": asset["currency"],
            "ISIN": asset["isin"],
        })

    return pd.DataFrame(rows)


# =========================================================
# SEARCH
# =========================================================

def search_kz_assets(query):
    """
    Search Kazakhstan assets by ticker,
    company name or sector.
    """

    catalog = get_kz_asset_catalog()

    if not query:
        return catalog

    query = query.lower().strip()

    mask = (
        catalog["Ticker"].str.lower().str.contains(
            query, regex=False
        )
        |
        catalog["Company"].str.lower().str.contains(
            query, regex=False
        )
        |
        catalog["Sector"].str.lower().str.contains(
            query, regex=False
        )
    )

    return catalog[mask]