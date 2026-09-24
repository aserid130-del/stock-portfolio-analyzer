import numpy as np
import pandas as pd
import streamlit as st

from data.market_data import get_prices

from views.dashboard import render_dashboard
from views.kazakhstan import render_kazakhstan
from views.analysis import render_analysis


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Market Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# GLOBAL UI
# =========================================================

st.markdown(
    """
    <style>

    /* Main page */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.20);
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 12px;
        padding: 14px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Reduce excessive whitespace */
    h1 {
        margin-bottom: 0.2rem;
    }

    h2, h3 {
        margin-top: 0.8rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    "## Market Terminal"
)

st.sidebar.caption(
    "Global markets · Kazakhstan · Analytics"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Stocks",
        "Kazakhstan",
        "Portfolio",
        "Analysis",
    ],
)

st.sidebar.divider()

st.sidebar.caption(
    "More modules coming:"
)

st.sidebar.caption(
    "Markets · Screener · Compare · Forecast · Watchlist"
)


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    render_dashboard()


# =========================================================
# STOCK EXPLORER
# =========================================================

elif page == "Stocks":

    st.title(
        "Asset Explorer"
    )

    st.caption(
        "Search and analyze global market instruments."
    )

    # -----------------------------------------------------
    # INPUTS
    # -----------------------------------------------------

    input_col1, input_col2 = st.columns(
        [3, 1]
    )

    with input_col1:

        ticker = (
            st.text_input(
                "Ticker",
                value="AAPL",
                placeholder=(
                    "AAPL, MSFT, NVDA, TSLA, BTC-USD..."
                ),
            )
            .strip()
            .upper()
        )

    with input_col2:

        period = st.selectbox(
            "Period",
            [
                "1mo",
                "3mo",
                "6mo",
                "1y",
                "2y",
                "5y",
            ],
            index=3,
        )

    analyze = st.button(
        "Analyze Asset",
        type="primary",
        width="stretch",
    )

    if analyze:

        if not ticker:

            st.error(
                "Enter a ticker."
            )

            st.stop()

        # -------------------------------------------------
        # DATA
        # -------------------------------------------------

        with st.spinner(
            f"Loading {ticker}..."
        ):

            try:

                prices = get_prices(
                    ticker,
                    period,
                )

            except Exception:

                st.error(
                    "Could not connect to the market-data provider."
                )

                st.stop()

        if (
            prices.empty
            or ticker not in prices.columns
        ):

            st.error(
                f"No historical market data was found for {ticker}."
            )

            st.stop()

        series = (
            prices[ticker]
            .dropna()
        )

        if len(series) < 2:

            st.error(
                "Not enough observations for analysis."
            )

            st.stop()

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        current_price = (
            series.iloc[-1]
        )

        previous_price = (
            series.iloc[-2]
        )

        start_price = (
            series.iloc[0]
        )

        daily_change = (
            current_price
            / previous_price
            - 1
        ) * 100

        total_return = (
            current_price
            / start_price
            - 1
        ) * 100

        daily_returns = (
            series
            .pct_change()
            .dropna()
        )

        volatility = (
            daily_returns.std()
            * np.sqrt(252)
            * 100
        )

        high_price = (
            series.max()
        )

        low_price = (
            series.min()
        )

        metric1, metric2, metric3, metric4 = (
            st.columns(4)
        )

        metric1.metric(
            "Price",
            f"${current_price:,.2f}",
            f"{daily_change:.2f}%",
        )

        metric2.metric(
            "Period Return",
            f"{total_return:.2f}%",
        )

        metric3.metric(
            "Volatility",
            f"{volatility:.2f}%",
        )

        metric4.metric(
            "Range",
            (
                f"${low_price:,.2f} – "
                f"${high_price:,.2f}"
            ),
        )

        # -------------------------------------------------
        # PRICE CHART
        # -------------------------------------------------

        st.subheader(
            f"{ticker} Market Price"
        )

        import plotly.graph_objects as go

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                name=ticker,
                hovertemplate=(
                    "%{x}<br>"
                    "Price: $%{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            height=520,
            hovermode="x unified",
            xaxis_title=None,
            yaxis_title="Price",
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20,
            ),
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

        # -------------------------------------------------
        # RETURNS
        # -------------------------------------------------

        left, right = st.columns(2)

        with left:

            st.subheader(
                "Return Distribution"
            )

            fig_returns = go.Figure()

            fig_returns.add_trace(
                go.Histogram(
                    x=daily_returns * 100,
                    nbinsx=40,
                    name="Daily Return",
                )
            )

            fig_returns.update_layout(
                height=350,
                xaxis_title="Daily Return (%)",
                yaxis_title="Observations",
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20,
                ),
            )

            st.plotly_chart(
                fig_returns,
                width="stretch",
            )

        with right:

            st.subheader(
                "Recent Market Data"
            )

            recent = pd.DataFrame(
                {
                    "Price":
                        series,

                    "Daily Return (%)":
                        series
                        .pct_change()
                        * 100,
                }
            ).tail(15)

            st.dataframe(
                recent,
                width="stretch",
            )


# =========================================================
# KAZAKHSTAN
# =========================================================

elif page == "Kazakhstan":

    render_kazakhstan()


# =========================================================
# PORTFOLIO
# =========================================================

elif page == "Portfolio":

    st.title(
        "Portfolio Builder"
    )

    st.caption(
        "Build and track an equal-weight global portfolio."
    )

    # -----------------------------------------------------
    # INPUTS
    # -----------------------------------------------------

    tickers_input = st.text_input(
        "Assets",
        value="AAPL, MSFT, NVDA, GOOGL, AMZN",
        placeholder="AAPL, MSFT, NVDA...",
    )

    input1, input2 = st.columns(2)

    with input1:

        investment = st.number_input(
            "Initial Investment ($)",
            min_value=100.0,
            value=10000.0,
            step=500.0,
        )

    with input2:

        period = st.selectbox(
            "Period",
            [
                "6mo",
                "1y",
                "2y",
                "5y",
            ],
            index=1,
        )

    build = st.button(
        "Build Portfolio",
        type="primary",
        width="stretch",
    )

    if build:

        tickers = [
            ticker.strip().upper()
            for ticker
            in tickers_input.split(",")
            if ticker.strip()
        ]

        if not tickers:

            st.error(
                "Enter at least one asset."
            )

            st.stop()

        # -------------------------------------------------
        # DATA
        # -------------------------------------------------

        with st.spinner(
            "Building portfolio..."
        ):

            try:

                prices = get_prices(
                    tickers,
                    period,
                )

            except Exception:

                st.error(
                    "Could not connect to the market-data provider."
                )

                st.stop()

        valid_tickers = [
            ticker
            for ticker in tickers
            if ticker in prices.columns
        ]

        invalid_tickers = [
            ticker
            for ticker in tickers
            if ticker not in valid_tickers
        ]

        if invalid_tickers:

            st.warning(
                "No usable historical data for: "
                + ", ".join(
                    invalid_tickers
                )
            )

        if not valid_tickers:

            st.error(
                "No assets with usable historical data were found."
            )

            st.stop()

        prices = (
            prices[
                valid_tickers
            ]
            .ffill()
            .dropna()
        )

        if len(prices) < 2:

            st.error(
                "Not enough historical observations."
            )

            st.stop()

        # -------------------------------------------------
        # PORTFOLIO MODEL
        # -------------------------------------------------

        normalized = (
            prices
            / prices.iloc[0]
        )

        weight = (
            1
            / len(valid_tickers)
        )

        portfolio_index = (
            normalized
            * weight
        ).sum(
            axis=1
        )

        portfolio_value = (
            portfolio_index
            * investment
        )

        final_value = (
            portfolio_value.iloc[-1]
        )

        profit = (
            final_value
            - investment
        )

        total_return = (
            final_value
            / investment
            - 1
        ) * 100

        portfolio_returns = (
            portfolio_value
            .pct_change()
            .dropna()
        )

        volatility = (
            portfolio_returns.std()
            * np.sqrt(252)
            * 100
        )

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        m1, m2, m3, m4 = (
            st.columns(4)
        )

        m1.metric(
            "Initial Capital",
            f"${investment:,.2f}",
        )

        m2.metric(
            "Portfolio Value",
            f"${final_value:,.2f}",
        )

        m3.metric(
            "Profit / Loss",
            f"${profit:,.2f}",
        )

        m4.metric(
            "Return",
            f"{total_return:.2f}%",
        )

        st.caption(
            f"Annualized volatility: {volatility:.2f}%"
        )

        # -------------------------------------------------
        # VISUALS
        # -------------------------------------------------

        import plotly.graph_objects as go

        chart_col, allocation_col = (
            st.columns(
                [3, 1]
            )
        )

        with chart_col:

            st.subheader(
                "Portfolio Performance"
            )

            fig_portfolio = go.Figure()

            fig_portfolio.add_trace(
                go.Scatter(
                    x=portfolio_value.index,
                    y=portfolio_value.values,
                    mode="lines",
                    name="Portfolio",
                    hovertemplate=(
                        "%{x}<br>"
                        "Value: $%{y:,.2f}"
                        "<extra></extra>"
                    ),
                )
            )

            fig_portfolio.add_hline(
                y=investment,
                line_dash="dash",
            )

            fig_portfolio.update_layout(
                height=450,
                xaxis_title=None,
                yaxis_title="Portfolio Value ($)",
                hovermode="x unified",
            )

            st.plotly_chart(
                fig_portfolio,
                width="stretch",
            )

        with allocation_col:

            st.subheader(
                "Allocation"
            )

            allocation = pd.DataFrame(
                {
                    "Ticker":
                        valid_tickers,

                    "Weight":
                        [
                            weight * 100
                            for _
                            in valid_tickers
                        ],
                }
            )

            fig_allocation = go.Figure(
                data=[
                    go.Pie(
                        labels=allocation[
                            "Ticker"
                        ],
                        values=allocation[
                            "Weight"
                        ],
                        hole=0.55,
                        textinfo="label+percent",
                    )
                ]
            )

            fig_allocation.update_layout(
                height=450,
                margin=dict(
                    l=10,
                    r=10,
                    t=10,
                    b=10,
                ),
            )

            st.plotly_chart(
                fig_allocation,
                width="stretch",
            )

        # -------------------------------------------------
        # ASSET COMPARISON
        # -------------------------------------------------

        st.subheader(
            "Asset Performance"
        )

        normalized_percent = (
            normalized
            * 100
        )

        fig_assets = go.Figure()

        for ticker in valid_tickers:

            fig_assets.add_trace(
                go.Scatter(
                    x=normalized_percent.index,
                    y=normalized_percent[
                        ticker
                    ],
                    mode="lines",
                    name=ticker,
                )
            )

        fig_assets.update_layout(
            height=450,
            xaxis_title=None,
            yaxis_title="Normalized Value",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_assets,
            width="stretch",
        )


# =========================================================
# ANALYSIS
# =========================================================

elif page == "Analysis":

    render_analysis()