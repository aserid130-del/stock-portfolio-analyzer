import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.market_data import get_prices
from providers.kase_provider import get_kase_instruments


# =========================================================
# CONFIG
# =========================================================

MARKET_STRIP = {
    "S&P 500": "^GSPC",
    "NASDAQ 100": "^NDX",
    "Bitcoin": "BTC-USD",
    "Gold": "GC=F",
    "Oil": "CL=F",
    "USD/KZT": "KZT=X",
}


MAIN_ASSETS = {
    "S&P 500": "^GSPC",
    "NASDAQ 100": "^NDX",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Tesla": "TSLA",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Gold": "GC=F",
    "Crude Oil": "CL=F",
    "USD/KZT": "KZT=X",
}


MOVERS_UNIVERSE = [
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "AVGO",
    "AMD",
    "NFLX",
    "JPM",
    "V",
    "MA",
    "ORCL",
    "CRM",
    "INTC",
]


MARKET_TABLE_ASSETS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Alphabet": "GOOGL",
    "Amazon": "AMZN",
    "Meta": "META",
    "Tesla": "TSLA",
    "Bitcoin": "BTC-USD",
    "Gold": "GC=F",
    "S&P 500": "^GSPC",
    "NASDAQ 100": "^NDX",
    "USD/KZT": "KZT=X",
}


# =========================================================
# CACHE
# =========================================================

@st.cache_data(ttl=300)
def load_market_prices(tickers, period):
    return get_prices(
        list(tickers),
        period=period
    )


@st.cache_data(ttl=900)
def load_kase_snapshot():
    return get_kase_instruments()


# =========================================================
# HELPERS
# =========================================================

def calculate_change(series):
    series = series.dropna()

    if len(series) < 2:
        return np.nan

    return (
        series.iloc[-1]
        / series.iloc[-2]
        - 1
    ) * 100


def calculate_period_return(series):
    series = series.dropna()

    if len(series) < 2:
        return np.nan

    return (
        series.iloc[-1]
        / series.iloc[0]
        - 1
    ) * 100


def calculate_volatility(series):
    returns = (
        series
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return np.nan

    return (
        returns.std()
        * np.sqrt(252)
        * 100
    )


def format_price(value):

    if pd.isna(value):
        return "N/A"

    if abs(value) >= 1000:
        return f"{value:,.2f}"

    return f"{value:.2f}"


# =========================================================
# PAGE
# =========================================================

def render_dashboard():

    # =====================================================
    # HEADER
    # =====================================================

    title_col, status_col = st.columns(
        [4, 1]
    )

    with title_col:

        st.title(
            "Market Terminal"
        )

        st.caption(
            "Global markets, Kazakhstan securities "
            "and portfolio analytics in one workspace."
        )

    with status_col:

        st.metric(
            "Data Mode",
            "Live / Delayed"
        )

    # =====================================================
    # MARKET STRIP
    # =====================================================

    with st.spinner(
        "Loading global markets..."
    ):

        strip_prices = load_market_prices(
            tuple(
                MARKET_STRIP.values()
            ),
            "5d"
        )

    st.subheader(
        "Global Markets"
    )

    strip_columns = st.columns(
        len(MARKET_STRIP)
    )

    for index, (
        name,
        ticker
    ) in enumerate(
        MARKET_STRIP.items()
    ):

        if (
            strip_prices.empty
            or ticker
            not in strip_prices.columns
        ):

            strip_columns[
                index
            ].metric(
                name,
                "N/A"
            )

            continue

        series = (
            strip_prices[ticker]
            .dropna()
        )

        if series.empty:

            strip_columns[
                index
            ].metric(
                name,
                "N/A"
            )

            continue

        current = (
            series.iloc[-1]
        )

        change = (
            calculate_change(
                series
            )
        )

        delta = (
            f"{change:.2f}%"
            if pd.notna(change)
            else None
        )

        strip_columns[
            index
        ].metric(
            name,
            format_price(
                current
            ),
            delta
        )

    st.divider()

    # =====================================================
    # MAIN AREA
    # =====================================================

    chart_column, mover_column = (
        st.columns(
            [3, 1]
        )
    )

    # =====================================================
    # MAIN CHART
    # =====================================================

    with chart_column:

        control1, control2 = (
            st.columns(
                [2, 1]
            )
        )

        with control1:

            selected_name = (
                st.selectbox(
                    "Main Market",
                    list(
                        MAIN_ASSETS.keys()
                    ),
                    index=0
                )
            )

        with control2:

            selected_period = (
                st.selectbox(
                    "Period",
                    [
                        "1mo",
                        "3mo",
                        "6mo",
                        "1y",
                        "2y",
                        "5y"
                    ],
                    index=3
                )
            )

        selected_ticker = (
            MAIN_ASSETS[
                selected_name
            ]
        )

        with st.spinner(
            f"Loading {selected_name}..."
        ):

            chart_prices = (
                load_market_prices(
                    (
                        selected_ticker,
                    ),
                    selected_period
                )
            )

        if (
            not chart_prices.empty
            and selected_ticker
            in chart_prices.columns
        ):

            series = (
                chart_prices[
                    selected_ticker
                ]
                .dropna()
            )

            if not series.empty:

                current_price = (
                    series.iloc[-1]
                )

                period_return = (
                    calculate_period_return(
                        series
                    )
                )

                chart_metric1, chart_metric2 = (
                    st.columns(2)
                )

                chart_metric1.metric(
                    selected_name,
                    format_price(
                        current_price
                    )
                )

                chart_metric2.metric(
                    "Period Return",
                    (
                        f"{period_return:.2f}%"
                        if pd.notna(
                            period_return
                        )
                        else "N/A"
                    )
                )

                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=series.index,
                        y=series.values,
                        mode="lines",
                        name=selected_name,
                        hovertemplate=(
                            "%{x}<br>"
                            "Price: %{y:,.2f}"
                            "<extra></extra>"
                        )
                    )
                )

                fig.update_layout(
                    height=470,
                    margin=dict(
                        l=10,
                        r=10,
                        t=25,
                        b=10
                    ),
                    xaxis_title=None,
                    yaxis_title=None,
                    hovermode="x unified",
                    showlegend=False,
                )

                fig.update_xaxes(
                    showgrid=False
                )

                st.plotly_chart(
                    fig,
                    width="stretch"
                )

        else:

            st.warning(
                "Market data is currently unavailable."
            )

    # =====================================================
    # TOP MOVERS
    # =====================================================

    with mover_column:

        st.markdown(
            "### Market Movers"
        )

        with st.spinner(
            "Loading movers..."
        ):

            mover_prices = (
                load_market_prices(
                    tuple(
                        MOVERS_UNIVERSE
                    ),
                    "5d"
                )
            )

        mover_rows = []

        if not mover_prices.empty:

            for ticker in (
                MOVERS_UNIVERSE
            ):

                if ticker not in (
                    mover_prices.columns
                ):
                    continue

                series = (
                    mover_prices[
                        ticker
                    ]
                    .dropna()
                )

                if len(series) < 2:
                    continue

                mover_rows.append({
                    "Ticker":
                        ticker,

                    "Price":
                        series.iloc[-1],

                    "Change":
                        calculate_change(
                            series
                        ),
                })

        movers = pd.DataFrame(
            mover_rows
        )

        if not movers.empty:

            gainers = (
                movers
                .sort_values(
                    "Change",
                    ascending=False
                )
                .head(5)
            )

            losers = (
                movers
                .sort_values(
                    "Change"
                )
                .head(5)
            )

            st.caption(
                "Top Gainers"
            )

            for _, row in (
                gainers.iterrows()
            ):

                left, right = (
                    st.columns(
                        [2, 1]
                    )
                )

                left.write(
                    f"**{row['Ticker']}**"
                )

                right.write(
                    f"+{row['Change']:.2f}%"
                )

            st.divider()

            st.caption(
                "Top Losers"
            )

            for _, row in (
                losers.iterrows()
            ):

                left, right = (
                    st.columns(
                        [2, 1]
                    )
                )

                left.write(
                    f"**{row['Ticker']}**"
                )

                right.write(
                    f"{row['Change']:.2f}%"
                )

        else:

            st.info(
                "Mover data unavailable."
            )

    st.divider()

    # =====================================================
    # MARKET OVERVIEW TABLE
    # =====================================================

    st.subheader(
        "Market Overview"
    )

    with st.spinner(
        "Building market overview..."
    ):

        table_prices = (
            load_market_prices(
                tuple(
                    MARKET_TABLE_ASSETS.values()
                ),
                "1y"
            )
        )

    market_rows = []

    for name, ticker in (
        MARKET_TABLE_ASSETS.items()
    ):

        if (
            table_prices.empty
            or ticker
            not in table_prices.columns
        ):
            continue

        series = (
            table_prices[
                ticker
            ]
            .dropna()
        )

        if len(series) < 2:
            continue

        market_rows.append({
            "Asset":
                name,

            "Ticker":
                ticker,

            "Price":
                series.iloc[-1],

            "1D (%)":
                calculate_change(
                    series
                ),

            "Period Return (%)":
                calculate_period_return(
                    series
                ),

            "Volatility (%)":
                calculate_volatility(
                    series
                ),
        })

    market_table = pd.DataFrame(
        market_rows
    )

    if not market_table.empty:

        market_table = (
            market_table.round(2)
        )

        st.dataframe(
            market_table,
            width="stretch",
            hide_index=True,
            column_config={
                "Price":
                    st.column_config.NumberColumn(
                        format="%.2f"
                    ),

                "1D (%)":
                    st.column_config.NumberColumn(
                        format="%.2f%%"
                    ),

                "Period Return (%)":
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
    # RETURN COMPARISON
    # =====================================================

    if not market_table.empty:

        st.subheader(
            "Performance Comparison"
        )

        comparison = (
            market_table
            .sort_values(
                "Period Return (%)",
                ascending=True
            )
        )

        fig_bar = go.Figure()

        fig_bar.add_trace(
            go.Bar(
                x=comparison[
                    "Period Return (%)"
                ],
                y=comparison[
                    "Asset"
                ],
                orientation="h",
                text=[
                    f"{value:.1f}%"
                    for value
                    in comparison[
                        "Period Return (%)"
                    ]
                ],
                textposition="outside",
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Return: %{x:.2f}%"
                    "<extra></extra>"
                )
            )
        )

        fig_bar.update_layout(
            height=500,
            xaxis_title=(
                "Return (%)"
            ),
            yaxis_title=None,
            margin=dict(
                l=10,
                r=40,
                t=10,
                b=10
            ),
        )

        st.plotly_chart(
            fig_bar,
            width="stretch"
        )

    st.divider()

    # =====================================================
    # KAZAKHSTAN SNAPSHOT
    # =====================================================

    st.subheader(
        "Kazakhstan Market"
    )

    with st.spinner(
        "Loading KASE..."
    ):

        kase = (
            load_kase_snapshot()
        )

    if not kase.empty:

        kz1, kz2, kz3, kz4 = (
            st.columns(4)
        )

        kz1.metric(
            "KASE Instruments",
            len(kase)
        )

        if "Company" in kase.columns:

            kz2.metric(
                "Companies",
                kase[
                    "Company"
                ].nunique()
            )

        else:

            kz2.metric(
                "Companies",
                "N/A"
            )

        if "Currency" in kase.columns:

            kz3.metric(
                "Currencies",
                kase[
                    "Currency"
                ].nunique()
            )

        else:

            kz3.metric(
                "Currencies",
                "N/A"
            )

        if "Price" in kase.columns:

            kz4.metric(
                "Priced Instruments",
                kase[
                    "Price"
                ].notna().sum()
            )

        else:

            kz4.metric(
                "Priced Instruments",
                "N/A"
            )

        preferred_tickers = [
            "AIRA",
            "HSBK",
            "CCBN",
            "KZAP",
            "KMGZ",
            "KEGC",
            "KCEL",
            "KSPI",
        ]

        kz_table = (
            kase[
                kase[
                    "Ticker"
                ].isin(
                    preferred_tickers
                )
            ]
            .copy()
        )

        if not kz_table.empty:

            visible_columns = [
                column
                for column in [
                    "Ticker",
                    "Company",
                    "Currency",
                    "Price",
                    "Type",
                ]
                if column
                in kz_table.columns
            ]

            st.dataframe(
                kz_table[
                    visible_columns
                ],
                width="stretch",
                hide_index=True
            )

    else:

        st.warning(
            "KASE snapshot is currently unavailable."
        )

    # =====================================================
    # FOOTER
    # =====================================================

    st.caption(
        "Market information may be delayed. "
        "Analytics are based on historical data "
        "and are not investment recommendations."
    )