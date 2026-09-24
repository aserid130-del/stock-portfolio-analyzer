import yfinance as yf
import pandas as pd


# =========================================================
# ASSET CATALOG
# =========================================================

MARKET_ASSETS = {
    "US Indices": {
        "S&P 500": "^GSPC",
        "NASDAQ 100": "^NDX",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
    },

    "Global Indices": {
        "FTSE 100": "^FTSE",
        "DAX": "^GDAXI",
        "CAC 40": "^FCHI",
        "Nikkei 225": "^N225",
        "Hang Seng": "^HSI",
    },

    "Commodities": {
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Crude Oil WTI": "CL=F",
        "Natural Gas": "NG=F",
        "Copper": "HG=F",
    },

    "Currencies": {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "JPY=X",
        "USD/CHF": "CHF=X",
        "USD/CNY": "CNY=X",
        "USD/KZT": "KZT=X",
    },

    "Crypto": {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD",
        "BNB": "BNB-USD",
        "XRP": "XRP-USD",
    },

    "ETFs": {
        "S&P 500 ETF": "SPY",
        "NASDAQ 100 ETF": "QQQ",
        "Gold ETF": "GLD",
        "US Bonds ETF": "BND",
        "Emerging Markets ETF": "VWO",
    }
}


# =========================================================
# PRICE DATA
# =========================================================

def get_prices(tickers, period="1y"):
    """
    Download historical adjusted market prices.
    """

    if isinstance(tickers, str):
        tickers = [tickers]

    tickers = list(dict.fromkeys(tickers))

    if not tickers:
        return pd.DataFrame()

    try:
        data = yf.download(
            tickers,
            period=period,
            auto_adjust=True,
            progress=False,
            threads=True,
        )

        if data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            prices = data["Close"].copy()

        else:
            prices = data[["Close"]].copy()

            if len(tickers) == 1:
                prices.columns = tickers

        return prices.dropna(how="all")

    except Exception:
        return pd.DataFrame()


# =========================================================
# SINGLE ASSET
# =========================================================

def get_asset_history(ticker, period="1y"):

    prices = get_prices(ticker, period)

    if prices.empty:
        return pd.Series(dtype=float)

    if ticker in prices.columns:
        return prices[ticker].dropna()

    return prices.iloc[:, 0].dropna()


# =========================================================
# MARKET SNAPSHOT
# =========================================================

def get_market_snapshot(asset_group):

    if asset_group not in MARKET_ASSETS:
        return pd.DataFrame()

    assets = MARKET_ASSETS[asset_group]

    rows = []

    for name, ticker in assets.items():

        history = get_asset_history(
            ticker,
            period="5d"
        )

        if len(history) < 2:
            continue

        current_price = history.iloc[-1]
        previous_price = history.iloc[-2]

        daily_change = (
            current_price / previous_price - 1
        ) * 100

        rows.append({
            "Asset": name,
            "Ticker": ticker,
            "Price": current_price,
            "Daily Change (%)": daily_change
        })

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)

    result["Price"] = result["Price"].round(2)
    result["Daily Change (%)"] = (
        result["Daily Change (%)"].round(2)
    )

    return result


# =========================================================
# NORMALIZED PERFORMANCE
# =========================================================

def normalize_prices(prices):

    if prices.empty:
        return prices

    return prices / prices.iloc[0] * 100