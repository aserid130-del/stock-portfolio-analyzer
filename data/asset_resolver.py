import logging
import re

import pandas as pd

from providers.kase_provider import (
    get_kase_instruments,
    search_kase_instruments,
)

logger = logging.getLogger(__name__)


# =========================================================
# EXCEPTIONS
# =========================================================

class AssetResolverError(Exception):
    """Base error for asset resolution."""


class AssetNotFoundError(AssetResolverError):
    """Asset could not be identified."""


# =========================================================
# HELPERS
# =========================================================

def _clean_query(query):
    if query is None:
        return ""

    return str(query).strip()


def _looks_like_ticker(query):
    pattern = r"^[A-Za-z0-9\^\.\-\=\_]{1,20}$"

    return bool(
        re.match(
            pattern,
            query.strip()
        )
    )


def _kase_row_to_asset(row):

    return {
        "query": None,

        "ticker": str(
            row.get(
                "Ticker",
                ""
            )
        ).strip(),

        "company": str(
            row.get(
                "Company",
                ""
            )
        ).strip(),

        "exchange": "KASE",

        "provider": "kase",

        "currency": row.get(
            "Currency"
        ),

        "isin": row.get(
            "ISIN"
        ),

        "asset_type": row.get(
            "Type"
        ),
    }


# =========================================================
# KASE
# =========================================================

def resolve_kase_asset(
    query,
    instruments=None
):

    query = _clean_query(query)

    if not query:

        raise AssetNotFoundError(
            "Empty asset query."
        )

    if instruments is None:

        instruments = (
            get_kase_instruments()
        )

    if instruments.empty:

        return None

    normalized_query = (
        query.lower()
    )

    # -----------------------------------------------------
    # EXACT TICKER
    # -----------------------------------------------------

    ticker_match = instruments[
        instruments["Ticker"]
        .astype(str)
        .str.strip()
        .str.lower()
        == normalized_query
    ]

    if not ticker_match.empty:

        result = _kase_row_to_asset(
            ticker_match.iloc[0]
        )

        result["query"] = query

        return result

    # -----------------------------------------------------
    # EXACT COMPANY NAME
    # -----------------------------------------------------

    if "Company" in instruments.columns:

        company_match = instruments[
            instruments["Company"]
            .astype(str)
            .str.strip()
            .str.lower()
            == normalized_query
        ]

        if not company_match.empty:

            company_match = (
                company_match.copy()
            )

            # Prefer KZT security

            if "Currency" in company_match.columns:

                kzt_match = company_match[
                    company_match["Currency"]
                    .astype(str)
                    .str.upper()
                    == "KZT"
                ]

                if not kzt_match.empty:

                    company_match = (
                        kzt_match.copy()
                    )

            # Prefer base ticker:
            # AIRA instead of AIRAd

            company_match[
                "_ticker_length"
            ] = (
                company_match["Ticker"]
                .astype(str)
                .str.len()
            )

            company_match = (
                company_match.sort_values(
                    "_ticker_length"
                )
            )

            result = _kase_row_to_asset(
                company_match.iloc[0]
            )

            result["query"] = query

            return result

    # -----------------------------------------------------
    # PARTIAL SEARCH
    # -----------------------------------------------------

    search_results = (
        search_kase_instruments(
            query,
            instruments
        )
    )

    if search_results.empty:

        return None

    search_results = (
        search_results.copy()
    )

    if "Currency" in search_results.columns:

        kzt_results = search_results[
            search_results["Currency"]
            .astype(str)
            .str.upper()
            == "KZT"
        ]

        if not kzt_results.empty:

            search_results = (
                kzt_results.copy()
            )

    search_results[
        "_ticker_length"
    ] = (
        search_results["Ticker"]
        .astype(str)
        .str.len()
    )

    search_results = (
        search_results.sort_values(
            "_ticker_length"
        )
    )

    result = _kase_row_to_asset(
        search_results.iloc[0]
    )

    result["query"] = query

    return result


# =========================================================
# GLOBAL
# =========================================================

def resolve_global_asset(query):

    query = _clean_query(query)

    if not query:

        raise AssetNotFoundError(
            "Empty asset query."
        )

    if not _looks_like_ticker(query):

        return None

    ticker = query.upper()

    return {
        "query": query,
        "ticker": ticker,
        "company": ticker,
        "exchange": "GLOBAL",
        "provider": "global",
        "currency": None,
        "isin": None,
        "asset_type": None,
    }


# =========================================================
# MAIN RESOLVER
# =========================================================

def resolve_asset(
    query,
    kase_instruments=None
):

    query = _clean_query(query)

    if not query:

        raise AssetNotFoundError(
            "Asset query is empty."
        )

    # -----------------------------------------------------
    # TRY KASE
    # -----------------------------------------------------

    try:

        kase_asset = (
            resolve_kase_asset(
                query,
                instruments=kase_instruments
            )
        )

        if kase_asset is not None:

            logger.info(
                "Resolved '%s' as KASE asset %s",
                query,
                kase_asset["ticker"]
            )

            return kase_asset

    except Exception as error:

        logger.warning(
            "KASE resolution failed for '%s': %s",
            query,
            error
        )

    # -----------------------------------------------------
    # TRY GLOBAL
    # -----------------------------------------------------

    global_asset = (
        resolve_global_asset(
            query
        )
    )

    if global_asset is not None:

        logger.info(
            "Resolved '%s' as global ticker %s",
            query,
            global_asset["ticker"]
        )

        return global_asset

    raise AssetNotFoundError(
        f"Asset '{query}' could not be identified."
    )


# =========================================================
# MULTIPLE ASSETS
# =========================================================

def resolve_assets(
    queries,
    kase_instruments=None
):

    if isinstance(queries, str):

        queries = [
            item.strip()
            for item
            in queries.split(",")
            if item.strip()
        ]

    if kase_instruments is None:

        try:

            kase_instruments = (
                get_kase_instruments()
            )

        except Exception:

            kase_instruments = (
                pd.DataFrame()
            )

    resolved_assets = []

    errors = []

    for query in queries:

        try:

            asset = resolve_asset(
                query,
                kase_instruments=kase_instruments
            )

            resolved_assets.append(
                asset
            )

        except AssetNotFoundError as error:

            errors.append(
                {
                    "query": query,
                    "error": str(error),
                }
            )

    return (
        resolved_assets,
        errors
    )