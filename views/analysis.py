import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.analysis_data import load_analysis_data


# =========================================================
# HELPERS
# =========================================================

def _show_data_error(error):
    """
    Display a specific user-facing error
    depending on what went wrong.
    """

    code = error.get("code")
    query = error.get("query", "Unknown")
    ticker = error.get("ticker")
    message = error.get("message", "")

    if code == "asset_not_found":

        st.error(
            f"Asset not found: {query}"
        )

    elif code == "historical_unavailable":

        label = (
            f"{query} ({ticker})"
            if ticker
            else query
        )

        st.warning(
            f"{label} was found, but historical daily "
            f"price data is not connected yet."
        )

    elif code == "no_period_data":

        label = ticker or query

        st.error(
            f"No historical data for {label} "
            f"for the selected period."
        )

    elif code == "provider_error":

        label = ticker or query

        st.error(
            f"Could not connect to the market-data "
            f"provider for {label}. Try again later."
        )

    else:

        st.error(
            message
            or f"Unexpected error for {query}."
        )


def _format_company(asset):
    company = asset.get("company")
    ticker = asset.get("ticker")

    if not company or company == ticker:
        return ticker

    return company


# =========================================================
# PAGE
# =========================================================

def render_analysis():

    st.title("Portfolio Analysis")

    st.write(
        "Analyze portfolio return, volatility, "
        "drawdown, diversification and risk-adjusted performance."
    )

    # =====================================================
    # SESSION STATE
    # =====================================================

    if "analysis_tickers" not in st.session_state:
        st.session_state.analysis_tickers = (
            "AAPL, MSFT, NVDA, GOOGL, AMZN"
        )

    if "analysis_period" not in st.session_state:
        st.session_state.analysis_period = "1y"

    if "analysis_rf" not in st.session_state:
        st.session_state.analysis_rf = 4.0

    # =====================================================
    # INPUTS
    # =====================================================

    st.text_input(
        "Assets",
        key="analysis_tickers",
        placeholder=(
            "AAPL, MSFT, Air Astana, HSBK..."
        )
    )

    input_col1, input_col2 = st.columns(2)

    with input_col1:

        periods = [
            "1mo",
            "3mo",
            "6mo",
            "1y",
            "2y",
            "5y"
        ]

        current_period = (
            st.session_state.analysis_period
        )

        period_index = (
            periods.index(current_period)
            if current_period in periods
            else 3
        )

        period = st.selectbox(
            "Analysis Period",
            periods,
            index=period_index,
            key="analysis_period_selector"
        )

        st.session_state.analysis_period = period

    with input_col2:

        risk_free_rate = st.number_input(
            "Risk-Free Rate (%)",
            min_value=0.0,
            max_value=30.0,
            value=float(
                st.session_state.analysis_rf
            ),
            step=0.25,
            key="analysis_rf_input"
        )

        st.session_state.analysis_rf = (
            risk_free_rate
        )

    run_analysis = st.button(
        "Run Analysis",
        type="primary"
    )

    if not run_analysis:
        return

    # =====================================================
    # PARSE INPUT
    # =====================================================

    queries = [
        item.strip()
        for item
        in st.session_state.analysis_tickers.split(",")
        if item.strip()
    ]

    if not queries:

        st.error(
            "Enter at least one asset."
        )

        return

    # =====================================================
    # LOAD DATA
    # =====================================================

    with st.spinner(
        "Loading market data..."
    ):

        prices, assets, errors = (
            load_analysis_data(
                queries,
                period=period
            )
        )

    # =====================================================
    # DATA ERRORS
    # =====================================================

    if errors:

        st.subheader(
            "Data Availability"
        )

        for error in errors:
            _show_data_error(error)

    if prices.empty:

        st.error(
            "No assets with usable historical "
            "price data were loaded."
        )

        return

    # =====================================================
    # CLEAN PRICES
    # =====================================================

    prices = (
        prices
        .sort_index()
        .ffill()
        .dropna()
    )

    if len(prices) < 2:

        st.error(
            "Not enough observations to calculate "
            "portfolio statistics."
        )

        return

    valid_tickers = (
        prices.columns.tolist()
    )

    loaded_asset_map = {
        asset["ticker"]: asset
        for asset in assets
        if asset.get("ticker")
        in valid_tickers
    }

    # =====================================================
    # RETURNS
    # =====================================================

    returns = (
        prices
        .pct_change(
            fill_method=None
        )
        .dropna()
    )

    if returns.empty:

        st.error(
            "Could not calculate returns "
            "from the loaded price data."
        )

        return

    # =====================================================
    # EQUAL WEIGHTS
    # =====================================================

    number_of_assets = len(
        valid_tickers
    )

    weights = pd.Series(
        np.repeat(
            1 / number_of_assets,
            number_of_assets
        ),
        index=valid_tickers
    )

    portfolio_returns = (
        returns
        .mul(
            weights,
            axis=1
        )
        .sum(axis=1)
    )

    # =====================================================
    # PORTFOLIO METRICS
    # =====================================================

    portfolio_growth = (
        1 + portfolio_returns
    ).cumprod()

    total_return = (
        portfolio_growth.iloc[-1]
        - 1
    )

    observations = len(
        portfolio_returns
    )

    annualized_return = (
        portfolio_growth.iloc[-1]
        ** (
            252 / observations
        )
        - 1
    )

    annualized_volatility = (
        portfolio_returns.std()
        * np.sqrt(252)
    )

    risk_free_decimal = (
        risk_free_rate / 100
    )

    if annualized_volatility > 0:

        sharpe_ratio = (
            annualized_return
            - risk_free_decimal
        ) / annualized_volatility

    else:

        sharpe_ratio = np.nan

    running_max = (
        portfolio_growth
        .cummax()
    )

    drawdown = (
        portfolio_growth
        / running_max
        - 1
    )

    max_drawdown = (
        drawdown.min()
    )

    # =====================================================
    # METRICS
    # =====================================================

    st.divider()

    st.subheader(
        "Portfolio Overview"
    )

    metric1, metric2, metric3, metric4 = (
        st.columns(4)
    )

    metric1.metric(
        "Total Return",
        f"{total_return * 100:.2f}%"
    )

    metric2.metric(
        "Annualized Volatility",
        f"{annualized_volatility * 100:.2f}%"
    )

    metric3.metric(
        "Sharpe Ratio",
        (
            f"{sharpe_ratio:.2f}"
            if not np.isnan(sharpe_ratio)
            else "N/A"
        )
    )

    metric4.metric(
        "Maximum Drawdown",
        f"{max_drawdown * 100:.2f}%"
    )

    st.caption(
        f"Annualized return: "
        f"{annualized_return * 100:.2f}%"
    )

    # =====================================================
    # ASSET TABLE
    # =====================================================

    st.subheader(
        "Portfolio Assets"
    )

    asset_rows = []

    for ticker in valid_tickers:

        asset = loaded_asset_map.get(
            ticker,
            {}
        )

        ticker_returns = (
            returns[ticker]
        )

        ticker_total_return = (
            prices[ticker].iloc[-1]
            / prices[ticker].iloc[0]
            - 1
        )

        ticker_volatility = (
            ticker_returns.std()
            * np.sqrt(252)
        )

        asset_rows.append({
            "Ticker":
                ticker,

            "Company":
                _format_company(
                    asset
                ),

            "Exchange":
                asset.get(
                    "exchange",
                    "GLOBAL"
                ),

            "Weight (%)":
                weights[ticker]
                * 100,

            "Return (%)":
                ticker_total_return
                * 100,

            "Volatility (%)":
                ticker_volatility
                * 100,
        })

    asset_table = pd.DataFrame(
        asset_rows
    )

    st.dataframe(
        asset_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Weight (%)":
                st.column_config.NumberColumn(
                    format="%.2f%%"
                ),

            "Return (%)":
                st.column_config.NumberColumn(
                    format="%.2f%%"
                ),

            "Volatility (%)":
                st.column_config.NumberColumn(
                    format="%.2f%%"
                ),
        }
    )

    # =====================================================
    # CUMULATIVE PERFORMANCE
    # =====================================================

    st.subheader(
        "Portfolio Performance"
    )

    growth_percent = (
        portfolio_growth - 1
    ) * 100

    fig_growth = go.Figure()

    fig_growth.add_trace(
        go.Scatter(
            x=growth_percent.index,
            y=growth_percent.values,
            mode="lines",
            name="Portfolio",
            hovertemplate=(
                "%{x}<br>"
                "Cumulative return: "
                "%{y:.2f}%"
                "<extra></extra>"
            )
        )
    )

    fig_growth.add_hline(
        y=0,
        line_dash="dash"
    )

    fig_growth.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative Return (%)",
        hovermode="x unified",
        height=450
    )

    st.plotly_chart(
        fig_growth,
        width="stretch"
    )

    # =====================================================
    # INDIVIDUAL ASSET PERFORMANCE
    # =====================================================

    st.subheader(
        "Asset Performance"
    )

    normalized_assets = (
        prices
        / prices.iloc[0]
        * 100
    )

    fig_assets = go.Figure()

    for ticker in valid_tickers:

        fig_assets.add_trace(
            go.Scatter(
                x=normalized_assets.index,
                y=normalized_assets[ticker],
                mode="lines",
                name=ticker
            )
        )

    fig_assets.update_layout(
        xaxis_title="Date",
        yaxis_title="Normalized Value",
        hovermode="x unified",
        height=500
    )

    st.plotly_chart(
        fig_assets,
        width="stretch"
    )

    st.caption(
        "Each asset starts at 100, "
        "making relative performance comparable."
    )

    # =====================================================
    # DRAWDOWN
    # =====================================================

    st.subheader(
        "Portfolio Drawdown"
    )

    drawdown_percent = (
        drawdown * 100
    )

    fig_drawdown = go.Figure()

    fig_drawdown.add_trace(
        go.Scatter(
            x=drawdown_percent.index,
            y=drawdown_percent.values,
            mode="lines",
            fill="tozeroy",
            name="Drawdown",
            hovertemplate=(
                "%{x}<br>"
                "Drawdown: %{y:.2f}%"
                "<extra></extra>"
            )
        )
    )

    fig_drawdown.update_layout(
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        height=400
    )

    st.plotly_chart(
        fig_drawdown,
        width="stretch"
    )

    # =====================================================
    # CORRELATION
    # =====================================================

    st.subheader(
        "Asset Correlation"
    )

    correlation = (
        returns
        .corr()
        .round(2)
    )

    fig_correlation = go.Figure(
        data=go.Heatmap(
            z=correlation.values,
            x=correlation.columns,
            y=correlation.index,
            zmin=-1,
            zmax=1,
            text=correlation.values,
            texttemplate="%{text:.2f}",
            hovertemplate=(
                "%{y} / %{x}<br>"
                "Correlation: %{z:.2f}"
                "<extra></extra>"
            )
        )
    )

    fig_correlation.update_layout(
        height=500,
        xaxis_title="Asset",
        yaxis_title="Asset"
    )

    st.plotly_chart(
        fig_correlation,
        width="stretch"
    )

    # =====================================================
    # RISK VS RETURN
    # =====================================================

    st.subheader(
        "Risk vs Return"
    )

    risk_return_rows = []

    for ticker in valid_tickers:

        ticker_return = (
            prices[ticker].iloc[-1]
            / prices[ticker].iloc[0]
            - 1
        ) * 100

        ticker_volatility = (
            returns[ticker].std()
            * np.sqrt(252)
            * 100
        )

        risk_return_rows.append({
            "Ticker": ticker,
            "Return": ticker_return,
            "Volatility": ticker_volatility
        })

    risk_return_df = pd.DataFrame(
        risk_return_rows
    )

    fig_risk = go.Figure()

    fig_risk.add_trace(
        go.Scatter(
            x=risk_return_df[
                "Volatility"
            ],
            y=risk_return_df[
                "Return"
            ],
            mode="markers+text",
            text=risk_return_df[
                "Ticker"
            ],
            textposition="top center",
            marker=dict(
                size=12
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Volatility: %{x:.2f}%<br>"
                "Return: %{y:.2f}%"
                "<extra></extra>"
            )
        )
    )

    fig_risk.update_layout(
        xaxis_title=(
            "Annualized Volatility (%)"
        ),
        yaxis_title=(
            "Period Return (%)"
        ),
        height=500
    )

    st.plotly_chart(
        fig_risk,
        width="stretch"
    )

    # =====================================================
    # TECHNICAL DETAILS
    # =====================================================

    with st.expander(
        "Data details"
    ):

        st.write(
            f"Loaded assets: "
            f"{', '.join(valid_tickers)}"
        )

        st.write(
            f"Observations: "
            f"{len(prices)}"
        )

        st.write(
            f"Selected period: "
            f"{period}"
        )

        st.write(
            f"Risk-free rate: "
            f"{risk_free_rate:.2f}%"
        )