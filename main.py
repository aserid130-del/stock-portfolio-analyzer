import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# -----------------------------
# PORTFOLIO SETTINGS
# -----------------------------

tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]

weights = pd.Series({
    "AAPL": 0.30,
    "MSFT": 0.25,
    "NVDA": 0.20,
    "GOOGL": 0.15,
    "AMZN": 0.10
})

initial_investment = 10000

# Assumed annual risk-free rate
risk_free_rate = 0.04


# -----------------------------
# DOWNLOAD MARKET DATA
# -----------------------------

stock = yf.download(tickers, period="1y")

close_prices = stock["Close"].dropna()


# -----------------------------
# PORTFOLIO VALUE
# -----------------------------

normalized = close_prices / close_prices.iloc[0]

portfolio_index = (normalized * weights).sum(axis=1)

portfolio_value = initial_investment * portfolio_index

final_value = portfolio_value.iloc[-1]

total_return = (
    final_value / initial_investment - 1
)


# -----------------------------
# RISK & RETURN METRICS
# -----------------------------

# Daily percentage returns
daily_returns = portfolio_value.pct_change().dropna()

# Number of trading days in a year
trading_days = 252

# Annualized return using compound growth
number_of_days = len(daily_returns)

annualized_return = (
    (final_value / initial_investment)
    ** (trading_days / number_of_days)
    - 1
)

# Annualized volatility
annualized_volatility = (
    daily_returns.std()
    * np.sqrt(trading_days)
)

# Sharpe Ratio
sharpe_ratio = (
    (annualized_return - risk_free_rate)
    / annualized_volatility
)


# -----------------------------
# RESULTS
# -----------------------------

print("\nPORTFOLIO ANALYSIS")
print("-" * 35)

print(f"Initial Investment:     ${initial_investment:,.2f}")
print(f"Final Portfolio Value:  ${final_value:,.2f}")

print(f"Total Return:           {total_return * 100:.2f}%")
print(f"Annualized Return:      {annualized_return * 100:.2f}%")
print(f"Annualized Volatility:  {annualized_volatility * 100:.2f}%")
print(f"Sharpe Ratio:           {sharpe_ratio:.2f}")


# -----------------------------
# CHART
# -----------------------------

plt.figure(figsize=(12, 6))

plt.plot(
    portfolio_value.index,
    portfolio_value,
    label="Portfolio"
)

plt.axhline(
    y=initial_investment,
    linestyle="--",
    label="Initial Investment"
)

plt.title("Portfolio Performance - Last 1 Year")
plt.xlabel("Date")
plt.ylabel("Portfolio Value (USD)")

plt.legend()
plt.grid(True)

plt.show()