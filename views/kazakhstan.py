import streamlit as st
import pandas as pd
import plotly.express as px

from providers.kase_provider import (
    get_kase_instruments,
    search_kase_instruments,
)


# =========================================================
# CACHE
# =========================================================

@st.cache_data(ttl=900)
def load_kase_data():
    return get_kase_instruments()


# =========================================================
# PAGE
# =========================================================

def render_kazakhstan():

    st.title("Kazakhstan Market")

    st.write(
        "Explore securities listed on the Kazakhstan Stock Exchange (KASE)."
    )

    # -----------------------------------------------------
    # LOAD DATA
    # -----------------------------------------------------

    with st.spinner("Loading KASE market data..."):
        instruments = load_kase_data()

    if instruments.empty:

        st.error(
            "KASE market data could not be loaded."
        )

        return

    # =====================================================
    # TOP METRICS
    # =====================================================

    total_assets = len(instruments)

    if "Company" in instruments.columns:
        companies = instruments["Company"].nunique()
    else:
        companies = 0

    if "Currency" in instruments.columns:
        currencies = instruments["Currency"].nunique()
    else:
        currencies = 0

    if "Price" in instruments.columns:
        priced_assets = instruments["Price"].notna().sum()
    else:
        priced_assets = 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "KASE Instruments",
        total_assets
    )

    c2.metric(
        "Companies",
        companies
    )

    c3.metric(
        "Currencies",
        currencies
    )

    c4.metric(
        "Assets With Price",
        priced_assets
    )

    st.divider()

    # =====================================================
    # SEARCH
    # =====================================================

    st.subheader("Search Securities")

    search_query = st.text_input(
        "Search by company, ticker or ISIN",
        placeholder="Air Astana, Halyk, AIRA, HSBK..."
    )

    if search_query:

        filtered = search_kase_instruments(
            search_query,
            instruments
        )

    else:

        filtered = instruments.copy()

    st.caption(
        f"Found: {len(filtered)} instruments"
    )

    # =====================================================
    # SEARCH RESULTS TABLE
    # =====================================================

    table_columns = [
        column
        for column in [
            "Ticker",
            "Company",
            "Type",
            "Currency",
            "Price",
            "Volume",
            "Date",
            "ISIN"
        ]
        if column in filtered.columns
    ]

    st.dataframe(
        filtered[table_columns],
        width="stretch",
        hide_index=True
    )

    st.divider()

    # =====================================================
    # MARKET STRUCTURE
    # =====================================================

    st.subheader("Market Structure")

    left, right = st.columns(2)

    # -----------------------------------------------------
    # PIE / DONUT CHART
    # -----------------------------------------------------

    with left:

        st.markdown("### Securities by Type")

        if "Type" in instruments.columns:

            type_distribution = (
                instruments["Type"]
                .fillna("Unknown")
                .replace("nan", "Unknown")
                .value_counts()
                .reset_index()
            )

            type_distribution.columns = [
                "Type",
                "Assets"
            ]

            fig_type = px.pie(
                type_distribution,
                names="Type",
                values="Assets",
                hole=0.42
            )

            fig_type.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Assets: %{value}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                )
            )

            fig_type.update_layout(
                legend_title_text="Security Type",
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20
                )
            )

            st.plotly_chart(
                fig_type,
                width="stretch"
            )

        else:

            st.info(
                "Security type data is unavailable."
            )

    # -----------------------------------------------------
    # CURRENCY CHART
    # -----------------------------------------------------

    with right:

        st.markdown("### Securities by Currency")

        if "Currency" in instruments.columns:

            currency_distribution = (
                instruments["Currency"]
                .fillna("Unknown")
                .replace("nan", "Unknown")
                .value_counts()
                .reset_index()
            )

            currency_distribution.columns = [
                "Currency",
                "Assets"
            ]

            fig_currency = px.bar(
                currency_distribution,
                x="Currency",
                y="Assets",
                text="Assets"
            )

            fig_currency.update_traces(
                textposition="outside"
            )

            fig_currency.update_layout(
                xaxis_title="Currency",
                yaxis_title="Number of Securities",
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20
                )
            )

            st.plotly_chart(
                fig_currency,
                width="stretch"
            )

        else:

            st.info(
                "Currency data is unavailable."
            )

    st.divider()

    # =====================================================
    # PRICE VISUALIZATION
    # =====================================================

    st.subheader("Market Prices")

    available_currencies = []

    if "Currency" in instruments.columns:

        available_currencies = sorted(
            instruments["Currency"]
            .dropna()
            .astype(str)
            .loc[
                lambda x:
                ~x.str.lower().eq("nan")
            ]
            .unique()
            .tolist()
        )

    if available_currencies:

        selected_currency = st.selectbox(
            "Currency",
            available_currencies,
            index=(
                available_currencies.index("KZT")
                if "KZT" in available_currencies
                else 0
            )
        )

        price_data = instruments.copy()

        price_data = price_data[
            price_data["Currency"]
            == selected_currency
        ]

        if "Price" in price_data.columns:

            price_data = price_data[
                price_data["Price"].notna()
            ]

            price_data = price_data[
                price_data["Price"] > 0
            ]

            price_data = price_data.sort_values(
                "Price",
                ascending=False
            )

            top_price_data = price_data.head(15)

            if not top_price_data.empty:

                fig_prices = px.bar(
                    top_price_data,
                    x="Price",
                    y="Ticker",
                    orientation="h",
                    hover_data=[
                        column
                        for column in [
                            "Company",
                            "Currency"
                        ]
                        if column
                        in top_price_data.columns
                    ]
                )

                fig_prices.update_layout(
                    yaxis={
                        "categoryorder":
                            "total ascending"
                    },
                    xaxis_title=(
                        f"Price ({selected_currency})"
                    ),
                    yaxis_title="Ticker",
                    height=600
                )

                st.plotly_chart(
                    fig_prices,
                    width="stretch"
                )

                st.caption(
                    "Top instruments by quoted price. "
                    "This is not market capitalization."
                )

            else:

                st.info(
                    "No price data available "
                    "for this currency."
                )

    st.divider()

    # =====================================================
    # COMPANY EXPLORER
    # =====================================================

    st.subheader("Company Explorer")

    if "Ticker" not in instruments.columns:
        return

    selector_data = instruments.copy()

    selector_data["Selector"] = (
        selector_data["Ticker"].astype(str)
        + " — "
        + selector_data["Company"].astype(str)
    )

    selected_asset = st.selectbox(
        "Select an instrument",
        selector_data["Selector"].tolist()
    )

    selected_row = selector_data[
        selector_data["Selector"]
        == selected_asset
    ].iloc[0]

    st.markdown(
        f"## {selected_row.get('Company', '')}"
    )

    info1, info2, info3, info4 = st.columns(4)

    info1.metric(
        "Ticker",
        selected_row.get(
            "Ticker",
            "N/A"
        )
    )

    info2.metric(
        "Price",
        (
            f"{selected_row.get('Price'):,.2f}"
            if pd.notna(
                selected_row.get("Price")
            )
            else "N/A"
        )
    )

    info3.metric(
        "Currency",
        selected_row.get(
            "Currency",
            "N/A"
        )
    )

    info4.metric(
        "Exchange",
        "KASE"
    )

    details = {
        "Company":
            selected_row.get(
                "Company",
                "N/A"
            ),

        "Ticker":
            selected_row.get(
                "Ticker",
                "N/A"
            ),

        "ISIN":
            selected_row.get(
                "ISIN",
                "N/A"
            ),

        "Security Type":
            selected_row.get(
                "Type",
                "N/A"
            ),

        "Currency":
            selected_row.get(
                "Currency",
                "N/A"
            ),

        "Last Price":
            selected_row.get(
                "Price",
                "N/A"
            ),

        "Volume":
            selected_row.get(
                "Volume",
                "N/A"
            ),

        "Market Date":
            selected_row.get(
                "Date",
                "N/A"
            ),
    }

    details_df = pd.DataFrame(
        details.items(),
        columns=[
            "Field",
            "Value"
        ]
    )

    st.dataframe(
        details_df,
        width="stretch",
        hide_index=True
    )

    st.caption(
        "Source: Kazakhstan Stock Exchange (KASE)."
    )