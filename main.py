import yfinance as yf
import matplotlib.pyplot as plt

ticker = "AAPL"

stock = yf.download(ticker, period="1y")

print(stock.head())

plt.figure(figsize=(12, 6))
plt.plot(stock.index, stock["Close"])

plt.title("Apple Stock Price - Last 1 Year")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.grid(True)

plt.show()