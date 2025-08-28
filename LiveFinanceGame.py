from colorama import init, Fore, Style
init(autoreset=True)
import json
import os
import matplotlib.pyplot as plt
import time
import yfinance as yf

START_BALANCE = 10000.0
DEFAULT_STOCKS = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOG", "NVDA", "PLTR"]

def get_historical_prices(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2y")
        if hist.empty:
            return []
        prices = [(str(date.date()), float(row["Close"])) for date, row in hist[::-1].iterrows()]
        return prices
    except Exception as e:
        print(f"Error fetching historical prices for {ticker}: {e}")
        return []

def get_performance(prices, days):
    if len(prices) < days:
        return None
    latest = prices[0][1]
    past = prices[days-1][1]
    change = ((latest - past) / past) * 100
    return change

def plot_price_graph(prices, title, days=None):
    if not prices:
        print("No data to plot.")
        return
    if days:
        prices = prices[:days]
    dates = [date for date, price in reversed(prices)]
    values = [price for date, price in reversed(prices)]
    plt.figure(figsize=(8, 4))
    plt.plot(dates, values, marker='o')
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Price ($)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"]
        if price.empty:
            print(f"Error: Ticker '{ticker}' not found or no price available.")
            return None
        return float(price.iloc[-1])
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None

def show_market_menu():
    print("\n--- Market Menu ---")
    for ticker in DEFAULT_STOCKS:
        price = get_price(ticker)
        prices = get_historical_prices(ticker)
        print(f"{ticker}: Current Price: ${price if price else 'N/A'}")
        if prices:
            day = get_performance(prices, 2)
            week = get_performance(prices, 5)
            month = get_performance(prices, 22)
            year = get_performance(prices, 252)
            print(f"  1D: {day:.2f}% | 1W: {week:.2f}% | 1M: {month:.2f}% | 1Y: {year:.2f}%")
        else:
            print("  No historical data available.")
    print("-------------------\n")
    ticker = input("Enter a ticker to view its graph (or press Enter to skip): ").strip().upper()
    if ticker:
        prices = get_historical_prices(ticker)
        if prices:
            plot_price_graph(prices, f"{ticker} - Last Year", days=252)
            plot_price_graph(prices, f"{ticker} - Last Week", days=5)
        else:
            print("No historical data available for that ticker.")

def show_stock_preview(ticker):
    price = get_price(ticker)
    prices = get_historical_prices(ticker)
    print(f"\nPreview for {ticker}:")
    print(f"Current Price: ${price if price else 'N/A'}")
    if prices:
        day = get_performance(prices, 2)
        week = get_performance(prices, 5)
        month = get_performance(prices, 22)
        year = get_performance(prices, 252)
        print(f"  1D: {day:.2f}% | 1W: {week:.2f}% | 1M: {month:.2f}% | 1Y: {year:.2f}%")
        plot_price_graph(prices, f"{ticker} - Last Year", days=252)
        plot_price_graph(prices, f"{ticker} - Last Week", days=5)
    else:
        print("  No historical data available.")

class Portfolio:
    def add_funds(self, amount):
        self.balance += amount
    def __init__(self, balance):
        self.balance = balance
        self.stocks = {}  # ticker: shares
        self.purchase_info = {}  # ticker: list of {"date": date, "price": price, "shares": shares}

    def buy(self, ticker, shares, price):
        cost = shares * price
        if cost > self.balance:
            print(f"Not enough balance! You have {self.balance:.2f} and you need {cost:.2f} to afford that stock!")
            return False
        self.balance -= cost
        self.stocks[ticker] = self.stocks.get(ticker, 0) + shares
        from datetime import datetime
        if ticker not in self.purchase_info:
            self.purchase_info[ticker] = []
        self.purchase_info[ticker].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "price": price,
            "shares": shares
        })
        print(f"Bought {shares} shares of {ticker} at ${price:.2f} each.")
        return True

    def sell(self, ticker, shares, price):
        if self.stocks.get(ticker, 0) < shares:
            print("Not enough shares!")
            return False
        self.stocks[ticker] -= shares
        self.balance += shares * price
        print(f"Sold {shares} shares of {ticker} at ${price:.2f} each.")
        return True

    def get_net_worth(self):
        total = self.balance
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            if price:
                total += shares * price
        return total

    def get_net_worth_change_since_last_save(self, filename="portfolio_save.json"):
        if not os.path.exists(filename):
            return None, None
        with open(filename, "r") as f:
            data = json.load(f)
        last_balance = data.get("balance", START_BALANCE)
        last_stocks = data.get("stocks", {})
        last_total = last_balance
        for ticker, shares in last_stocks.items():
            prices = get_historical_prices(ticker)
            last_price = prices[0][1] if prices else 0
            last_total += shares * last_price
        current_total = self.get_net_worth()
        change = current_total - last_total
        percent = (change / last_total * 100) if last_total else 0
        return change, percent

    def get_stock_performance_since_last_save(self, filename="portfolio_save.json"):
        if not os.path.exists(filename):
            return {}
        with open(filename, "r") as f:
            data = json.load(f)
        last_stocks = data.get("stocks", {})
        performance = {}
        for ticker, shares in self.stocks.items():
            prices = get_historical_prices(ticker)
            if not prices:
                performance[ticker] = "No historical data available."
                continue
            last_price = prices[0][1]
            current_price = get_price(ticker)
            if current_price is None:
                performance[ticker] = "Current price unavailable."
                continue
            change = ((current_price - last_price) / last_price) * 100 if last_price else 0
            if change > 0:
                color = Fore.GREEN
            elif change < 0:
                color = Fore.RED
            else:
                color = Style.RESET_ALL
            performance[ticker] = f"{shares} shares | Last: ${last_price:.2f} | Now: ${current_price:.2f} | Change: {color}{change:.2f}%{Style.RESET_ALL}"
        return performance

    def get_portfolio_change_since_purchase(self):
        summary = {}
        for ticker, shares in self.stocks.items():
            current_price = get_price(ticker)
            if ticker in self.purchase_info:
                total_purchased = sum([p["shares"] for p in self.purchase_info[ticker]])
                avg_purchase_price = sum([p["price"] * p["shares"] for p in self.purchase_info[ticker]]) / total_purchased if total_purchased else 0
                change = ((current_price - avg_purchase_price) / avg_purchase_price * 100) if avg_purchase_price else 0
                summary[ticker] = {
                    "shares": shares,
                    "avg_purchase_price": avg_purchase_price,
                    "current_price": current_price,
                    "change": change
                }
            else:
                summary[ticker] = "No purchase info."
        return summary

    def save(self, filename="portfolio_save.json"):
        data = {
            "balance": self.balance,
            "stocks": self.stocks,
            "purchase_info": self.purchase_info
        }
        with open(filename, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load(filename="portfolio_save.json"):
        if not os.path.exists(filename):
            return Portfolio(START_BALANCE)
        with open(filename, "r") as f:
            data = json.load(f)
        portfolio = Portfolio(data.get("balance", START_BALANCE))
        portfolio.stocks = data.get("stocks", {})
        portfolio.purchase_info = data.get("purchase_info", {})
        return portfolio

    def show(self):
        print(f"Balance: ${self.balance:.2f}")
        print(f"Net Worth: ${self.get_net_worth():.2f}")
        print("Portfolio:")
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            color = Style.RESET_ALL
            change_str = ""
            value_str = ""
            if hasattr(self, 'purchase_info') and ticker in self.purchase_info and self.purchase_info[ticker]:
                total_purchased = sum([p["shares"] for p in self.purchase_info[ticker]])
                avg_purchase_price = sum([p["price"] * p["shares"] for p in self.purchase_info[ticker]]) / total_purchased if total_purchased else 0
                change = ((price - avg_purchase_price) / avg_purchase_price * 100) if avg_purchase_price else 0
                value = shares * price if price is not None else 0
                if change > 0:
                    color = Fore.GREEN
                elif change < 0:
                    color = Fore.RED
                change_str = f" | Change: {color}{change:.2f}%{Style.RESET_ALL}"
                value_str = f" | Value: {color}${value:.2f}{Style.RESET_ALL}"
            print(f"  {color}{ticker}{Style.RESET_ALL}: {shares} shares{value_str}{change_str}")

    def show_market_value(self):
        total_value = 0.0
        print("\nCurrent Market Value of Portfolio:")
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            if price is not None:
                value = shares * price
                total_value += value
                print(f"  {ticker}: {shares} shares x ${price:.2f} = ${value:.2f}")
            else:
                print(f"  {ticker}: {shares} shares (price unavailable)")
        print(f"Total Market Value of Holdings: ${total_value:.2f}\n")

def main():
    print("Welcome to the Stock Trading Game!")
    while True:
        choice = input("Type 'new' to start a new game or 'continue' to load your previous game: ").strip().lower()
        if choice == "new":
            portfolio = Portfolio(START_BALANCE)
            print("Starting a new game!")
            break
        elif choice == "continue":
            portfolio = Portfolio.load()
            print("Continuing your previous game!")
            print("\n--- Portfolio Performance Since Last Save ---")
            change, percent = portfolio.get_net_worth_change_since_last_save()
            if change is not None:
                if change > 0:
                    color = Fore.GREEN
                elif change < 0:
                    color = Fore.RED
                else:
                    color = Style.RESET_ALL
                print(f"Net Worth Change Since Last Check-in: {color}${change:.2f} ({percent:.2f}%){Style.RESET_ALL}")
            print("\n--- Portfolio Change Since Purchase ---")
            purchase_summary = portfolio.get_portfolio_change_since_purchase()
            for ticker, info in purchase_summary.items():
                if isinstance(info, dict):
                    c = Fore.GREEN if info["change"] > 0 else (Fore.RED if info["change"] < 0 else Style.RESET_ALL)
                    print(f"{ticker}: {info['shares']} shares | Avg Purchase: ${info['avg_purchase_price']:.2f} | Now: ${info['current_price']:.2f} | Change: {c}{info['change']:.2f}%{Style.RESET_ALL}")
                else:
                    print(f"{ticker}: {info}")
            print("--------------------------------------------\n")
            show_graph = input("Would you like to see a graph of your portfolio value over time? (yes/no): ").strip().lower()
            if show_graph == "yes":
                dates = []
                values = []
                for ticker, purchases in portfolio.purchase_info.items():
                    for p in purchases:
                        dates.append(p["date"])
                        values.append(p["price"] * p["shares"])
                if dates and values:
                    plt.figure(figsize=(8,4))
                    plt.plot(dates, values, marker='o')
                    plt.title("Portfolio Value at Purchase Dates")
                    plt.xlabel("Date")
                    plt.ylabel("Value ($)")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.show()
                else:
                    print("No purchase history to plot.")
            break
        else:
            print("Invalid choice. Please type 'new' or 'continue'.")

    while True:
        portfolio.show()
        portfolio.show_market_value()
        print("Type 'market' to view available stocks.")
        action = input("Buy, Sell, Market, or Quit? ").strip().lower()
        if action == "quit":
            portfolio.save()
            print("Progress saved. Goodbye!")
            break
        elif action == "market":
            show_market_menu()
            continue
        ticker = input("Enter stock ticker (e.g., AAPL): ").strip().upper()
        if action == "buy":
            DoubleCheckValue = input("Would you like to see graphs before you buy (yes/no)? ")
            if DoubleCheckValue.lower() == "yes":
                show_stock_preview(ticker)
            else:
                print("No graphs will be shown.")
            confirm = input("Do you want to proceed with the buy? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Buy cancelled.")
                continue
        price = get_price(ticker)
        if price is None:
            continue
        print(f"Current price of {ticker}: ${price:.2f}")
        shares = int(input("How many shares? "))
        if action == "buy":
            portfolio.buy(ticker, shares, price)
        elif action == "sell":
            portfolio.sell(ticker, shares, price)
        else:
            print("Invalid action.")
        print()
        time.sleep(1)

if __name__ == "__main__":
    main()
from colorama import init, Fore, Style
init(autoreset=True)
from sys import platform
import json
import os
import matplotlib.pyplot as plt
import time
import yfinance as yf

# Starting fictional balance
START_BALANCE = 10000.0

# List of default stocks for the market menu
DEFAULT_STOCKS = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOG", "NVDA", "PLTR"]

# Helper to get historical prices for a ticker using yfinance

# --- Clean Portfolio class ---
class Portfolio:
    def __init__(self, balance):
        self.balance = balance
        self.stocks = {}  # ticker: shares
        self.purchase_info = {}  # ticker: list of {"date": date, "price": price, "shares": shares}

    def buy(self, ticker, shares, price):
        cost = shares * price
        if cost > self.balance:
            print("Not enough balance!")
            return False
        self.balance -= cost
        self.stocks[ticker] = self.stocks.get(ticker, 0) + shares
        from datetime import datetime
        if ticker not in self.purchase_info:
            self.purchase_info[ticker] = []
        self.purchase_info[ticker].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "price": price,
            "shares": shares
        })
        print(f"Bought {shares} shares of {ticker} at ${price:.2f} each.")
        return True

    def sell(self, ticker, shares, price):
        if self.stocks.get(ticker, 0) < shares:
            print("Not enough shares!")
            return False
        self.stocks[ticker] -= shares
        self.balance += shares * price
        print(f"Sold {shares} shares of {ticker} at ${price:.2f} each.")
        return True

    def get_net_worth(self):
        total = self.balance
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            if price:
                total += shares * price
        return total

    def get_net_worth_change_since_last_save(self, filename="portfolio_save.json"):
        if not os.path.exists(filename):
            return None, None
        with open(filename, "r") as f:
            data = json.load(f)
        last_balance = data.get("balance", START_BALANCE)
        last_stocks = data.get("stocks", {})
        last_total = last_balance
        for ticker, shares in last_stocks.items():
            prices = get_historical_prices(ticker)
            last_price = prices[0][1] if prices else 0
            last_total += shares * last_price
        current_total = self.get_net_worth()
        change = current_total - last_total
        percent = (change / last_total * 100) if last_total else 0
        return change, percent

    def get_stock_performance_since_last_save(self, filename="portfolio_save.json"):
        if not os.path.exists(filename):
            return {}
        with open(filename, "r") as f:
            data = json.load(f)
        last_stocks = data.get("stocks", {})
        performance = {}
        for ticker, shares in self.stocks.items():
            prices = get_historical_prices(ticker)
            if not prices:
                performance[ticker] = "No historical data available."
                continue
            last_price = prices[0][1]
            current_price = get_price(ticker)
            if current_price is None:
                performance[ticker] = "Current price unavailable."
                continue
            change = ((current_price - last_price) / last_price) * 100 if last_price else 0
            if change > 0:
                color = Fore.GREEN
            elif change < 0:
                color = Fore.RED
            else:
                color = Style.RESET_ALL
            performance[ticker] = f"{shares} shares | Last: ${last_price:.2f} | Now: ${current_price:.2f} | Change: {color}{change:.2f}%{Style.RESET_ALL}"
        return performance

    def get_portfolio_change_since_purchase(self):
        summary = {}
        for ticker, shares in self.stocks.items():
            current_price = get_price(ticker)
            if ticker in self.purchase_info:
                total_purchased = sum([p["shares"] for p in self.purchase_info[ticker]])
                avg_purchase_price = sum([p["price"] * p["shares"] for p in self.purchase_info[ticker]]) / total_purchased if total_purchased else 0
                change = ((current_price - avg_purchase_price) / avg_purchase_price * 100) if avg_purchase_price else 0
                summary[ticker] = {
                    "shares": shares,
                    "avg_purchase_price": avg_purchase_price,
                    "current_price": current_price,
                    "change": change
                }
            else:
                summary[ticker] = "No purchase info."
        return summary

    def save(self, filename="portfolio_save.json"):
        data = {
            "balance": self.balance,
            "stocks": self.stocks,
            "purchase_info": self.purchase_info
        }
        with open(filename, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load(filename="portfolio_save.json"):
        if not os.path.exists(filename):
            return Portfolio(START_BALANCE)
        with open(filename, "r") as f:
            data = json.load(f)
        portfolio = Portfolio(data.get("balance", START_BALANCE))
        portfolio.stocks = data.get("stocks", {})
        portfolio.purchase_info = data.get("purchase_info", {})
        return portfolio

    def show(self):
        print(f"Balance: ${self.balance:.2f}")
        print(f"Net Worth: ${self.get_net_worth():.2f}")
        print("Portfolio:")
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            color = Style.RESET_ALL
            change_str = ""
            value_str = ""
            if ticker in self.purchase_info and self.purchase_info[ticker]:
                total_purchased = sum([p["shares"] for p in self.purchase_info[ticker]])
                avg_purchase_price = sum([p["price"] * p["shares"] for p in self.purchase_info[ticker]]) / total_purchased if total_purchased else 0
                change = ((price - avg_purchase_price) / avg_purchase_price * 100) if avg_purchase_price else 0
                value = shares * price if price is not None else 0
                if change > 0:
                    color = Fore.GREEN
                elif change < 0:
                    color = Fore.RED
                change_str = f" | Change: {color}{change:.2f}%{Style.RESET_ALL}"
                value_str = f" | Value: {color}${value:.2f}{Style.RESET_ALL}"
                print(f"  {color}{ticker}{Style.RESET_ALL}: {shares} shares{value_str}{change_str}")
            else:
                print(f"  {ticker}: {shares} shares | No purchase info")

    def show_market_value(self):
        total_value = 0.0
        print("\nCurrent Market Value of Portfolio:")
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            if price is not None:
                value = shares * price
                total_value += value
                print(f"  {ticker}: {shares} shares x ${price:.2f} = ${value:.2f}")
            else:
                print(f"  {ticker}: {shares} shares (price unavailable)")
        print(f"Total Market Value of Holdings: ${total_value:.2f}\n")
    def save(self, filename="portfolio_save.json"):
        data = {
            "balance": self.balance,
            "stocks": self.stocks
        }
        with open(filename, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load(filename="portfolio_save.json"):
        if not os.path.exists(filename):
            return Portfolio(START_BALANCE)
        with open(filename, "r") as f:
            data = json.load(f)
        portfolio = Portfolio(data.get("balance", START_BALANCE))
        portfolio.stocks = data.get("stocks", {})
        return portfolio
    def __init__(self, balance):
        self.balance = balance
        self.stocks = {}  # ticker: shares

    def buy(self, ticker, shares, price):
        cost = shares * price
        if cost > self.balance:
            print("Not enough balance!")
            return False
        self.balance -= cost
        self.stocks[ticker] = self.stocks.get(ticker, 0) + shares
        print(f"Bought {shares} shares of {ticker} at ${price:.2f} each.")
        return True

    def sell(self, ticker, shares, price):
        if self.stocks.get(ticker, 0) < shares:
            print("Not enough shares!")
            return False
        self.stocks[ticker] -= shares
        self.balance += shares * price
        print(f"Sold {shares} shares of {ticker} at ${price:.2f} each.")
        return True

    def get_net_worth(self):
        total_value = self.balance
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            if price is not None:
                total_value += shares * price
        return total_value

    def show(self):
        print(f"Balance: ${self.balance:.2f}")
        print(f"Net Worth: ${self.get_net_worth():.2f}")
        print("Portfolio:")
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            color = Style.RESET_ALL
            change_str = ""
            value_str = ""
            if ticker in self.purchase_info and self.purchase_info[ticker]:
                total_purchased = sum([p["shares"] for p in self.purchase_info[ticker]])
                avg_purchase_price = sum([p["price"] * p["shares"] for p in self.purchase_info[ticker]]) / total_purchased if total_purchased else 0
                change = ((price - avg_purchase_price) / avg_purchase_price * 100) if avg_purchase_price else 0
                value = shares * price if price is not None else 0
                if change > 0:
                    color = Fore.GREEN
                elif change < 0:
                    color = Fore.RED
                change_str = f" | Change: {color}{change:.2f}%{Style.RESET_ALL}"
                value_str = f" | Value: {color}${value:.2f}{Style.RESET_ALL}"
            print(f"  {color}{ticker}{Style.RESET_ALL}: {shares} shares{value_str}{change_str}")

    def show_market_value(self):
        total_value = 0.0
        print("\nCurrent Market Value of Portfolio:")
        for ticker, shares in self.stocks.items():
            price = get_price(ticker)
            if price is not None:
                value = shares * price
                total_value += value
                print(f"  {ticker}: {shares} shares x ${price:.2f} = ${value:.2f}")
            else:
                print(f"  {ticker}: {shares} shares (price unavailable)")
        print(f"Total Market Value of Holdings: ${total_value:.2f}\n")


def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"]
        if price.empty:
            print(f"Error: Ticker '{ticker}' not found or no price available.")
            return None
        return float(price.iloc[-1])
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None

def main():
    print("Welcome to the Stock Trading Game!")
    while True:
        choice = input("Type 'new' to start a new game or 'continue' to load your previous game: ").strip().lower()
        if choice == "new":
            portfolio = Portfolio(START_BALANCE)
            print("Starting a new game!")
            break
        elif choice == "continue":
            portfolio = Portfolio.load()
            print("Continuing your previous game!")
            # Show performance summary for owned stocks
            print("\n--- Portfolio Performance Since Last Save ---")
            change, percent = portfolio.get_net_worth_change_since_last_save()
            if change is not None:
                if change > 0:
                    color = Fore.GREEN
                elif change < 0:
                    color = Fore.RED
                else:
                    color = Style.RESET_ALL
                print(f"Net Worth Change: {color}${change:.2f} ({percent:.2f}%){Style.RESET_ALL}")
            perf = portfolio.get_stock_performance_since_last_save()
            if perf:
                for ticker, summary in perf.items():
                    print(f"{ticker}: {summary}")
            else:
                print("No stocks owned or no previous save data.")
            print("--------------------------------------------\n")
            break
        else:
            print("Invalid choice. Please type 'new' or 'continue'.")

    while True:
        portfolio.show()
        portfolio.show_market_value()
        print("Type 'market' to view available stocks.")
        action = input("Buy, Sell, Market, or Quit? ").strip().lower()
        if action == "quit":
            portfolio.save()
            print("Progress saved. Goodbye!")
            break
        elif action == "market":
            show_market_menu()
            continue
        ticker = input("Enter stock ticker (e.g., AAPL): ").strip().upper()
        if action == "buy":
            DoubleCheckValue = input("Would you like to see graphs before you buy (yes/no)? ")
            if DoubleCheckValue.lower() == "yes":
                show_stock_preview(ticker)
            else:
                print("No graphs will be shown.")
            confirm = input("Do you want to proceed with the buy? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Buy cancelled.")
                continue
        price = get_price(ticker)
        if price is None:
            continue
        print(f"Current price of {ticker}: ${price:.2f}")
        shares = int(input("How many shares? "))
        if action == "buy":
            portfolio.buy(ticker, shares, price)
        elif action == "sell":
            portfolio.sell(ticker, shares, price)
        elif action == "infinite_money":
            portfolio.add_funds(1000000)
            print("Infinite money activated!")
            portfolio.show()
            continue
        else:
            print("Invalid action.")
        print()
        time.sleep(1)  # Small delay for realism

if __name__ == "__main__":
    main()
