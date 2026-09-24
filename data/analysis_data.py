import logging

import pandas as pd
import yfinance as yf

from data.asset_resolver import (
    resolve_assets,
    AssetNotFoundError,
)


logger = logging.getLogger(__name__)


# =========================================================
# ERRORS
# =========================================================

class AnalysisDataError(Exception):
    """Base error for analysis data."""


class NoHistoricalDataError(AnalysisDataError):
    """Asset exists, but no data exists for selected period."""


class HistoricalDataUnavailableError(AnalysisDataError):
    """Historical data provider is not available for this asset."""


class DataProviderError(AnalysisDataError):
    """External market-data provider failed."""


# =========================================================
# GLOBAL HISTORICAL DATA
# =========================================================

def get_global_history(ticker, period="1y"):
    """
    Download historical prices for a global asset.

    Returns:
        pandas.Series with closing prices.
    """

    try:

        data = yf.download(
            ticker,
            period=period,
            auto_adjust=True,
            progress=False,
            threads=False,
        )

    except Exception as error:

        logger.exception(
            "Global provider failed for %s",
            ticker
        )

        raise DataProviderError(
            f"Could not connect to the market-data provider "
            f"for {ticker}."
        ) from error

    if data is None or data.empty:

        raise NoHistoricalDataError(
            f"No historical data is available for "
            f"{ticker} for period {period}."
        )

    try:

        if isinstance(
            data.columns,
            pd.MultiIndex
        ):

            close = data["Close"]

            if isinstance(
                close,
                pd.DataFrame
            ):

                if ticker in close.columns:

                    close = close[ticker]

                else:

                    close = close.iloc[:, 0]

        else:

            close = data["Close"]

        close = (
            pd.Series(close)
            .dropna()
            .astype(float)
        )

    except Exception as error:

        logger.exception(
            "Could not parse price data for %s",
            ticker
        )

        raise DataProviderError(
            f"Market data for {ticker} "
            f"could not be processed."
        ) from error

    if len(close) < 2:

        raise NoHistoricalDataError(
            f"Not enough historical observations "
            f"for {ticker}."
        )

    close.name = ticker

    return close


# =========================================================
# SINGLE ASSET
# =========================================================

def get_asset_history(
    asset,
    period="1y"
):
    """
    Route an already-resolved asset
    to the correct provider.
    """

    provider = asset.get("provider")

    ticker = asset.get("ticker")

    company = asset.get(
        "company",
        ticker
    )

    # -----------------------------------------------------
    # GLOBAL
    # -----------------------------------------------------

    if provider == "global":

        return get_global_history(
            ticker,
            period
        )

    # -----------------------------------------------------
    # KASE
    # -----------------------------------------------------

    if provider == "kase":

        # KASE asset resolution works,
        # but our current KASE provider only contains
        # market snapshot/catalog information.
        #
        # Historical daily-price support will be
        # implemented separately.

        raise HistoricalDataUnavailableError(
            f"{company} ({ticker}) was found on KASE, "
            f"but historical daily price data is not yet "
            f"connected to Portfolio Analysis."
        )

    # -----------------------------------------------------
    # UNKNOWN PROVIDER
    # -----------------------------------------------------

    raise DataProviderError(
        f"Unknown data provider for {ticker}."
    )


# =========================================================
# MULTI-ASSET ANALYSIS DATA
# =========================================================

def load_analysis_data(
    queries,
    period="1y"
):
    """
    Resolve assets and load historical prices.

    Returns:
        prices       -> DataFrame
        assets       -> list of successfully loaded assets
        errors       -> list of readable error dictionaries
    """

    resolved_assets, resolver_errors = (
        resolve_assets(queries)
    )

    price_series = []

    loaded_assets = []

    errors = []

    # -----------------------------------------------------
    # RESOLVER ERRORS
    # -----------------------------------------------------

    for error in resolver_errors:

        errors.append({
            "query": error.get("query"),
            "code": "asset_not_found",
            "message": (
                f"Asset '{error.get('query')}' "
                f"could not be identified."
            ),
        })

    # -----------------------------------------------------
    # HISTORICAL DATA
    # -----------------------------------------------------

    for asset in resolved_assets:

        query = asset.get("query")
        ticker = asset.get("ticker")

        try:

            history = get_asset_history(
                asset,
                period
            )

            price_series.append(
                history.rename(ticker)
            )

            loaded_assets.append(
                asset
            )

        except HistoricalDataUnavailableError as error:

            errors.append({
                "query": query,
                "ticker": ticker,
                "code": "historical_unavailable",
                "message": str(error),
            })

        except NoHistoricalDataError as error:

            errors.append({
                "query": query,
                "ticker": ticker,
                "code": "no_period_data",
                "message": str(error),
            })

        except DataProviderError as error:

            errors.append({
                "query": query,
                "ticker": ticker,
                "code": "provider_error",
                "message": str(error),
            })

        except Exception as error:

            logger.exception(
                "Unexpected analysis error for %s",
                ticker
            )

            errors.append({
                "query": query,
                "ticker": ticker,
                "code": "unexpected_error",
                "message": (
                    f"Unexpected error while loading "
                    f"{ticker}: {error}"
                ),
            })

    # -----------------------------------------------------
    # CREATE DATAFRAME
    # -----------------------------------------------------

    if not price_series:

        return (
            pd.DataFrame(),
            loaded_assets,
            errors
        )

    prices = pd.concat(
        price_series,
        axis=1
    )

    prices = prices.sort_index()

    prices = prices.dropna(
        how="all"
    )

    return (
        prices,
        loaded_assets,
        errors
    )