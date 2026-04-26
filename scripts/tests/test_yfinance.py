import yfinance as yf
import json
import sys

def test_yfinance(symbol):
    print(f"Testing {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        print(f"Name: {info.get('longName', info.get('shortName', 'N/A'))}")

        price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("navPrice")
        print(f"Price: {price} {info.get('currency', 'N/A')}")

        # Sector allocations
        sectors = info.get('sectorWeightings', [])
        print(f"Sectors: {sectors[:2]}... (total {len(sectors)})")

        # Geo allocations
        holdings = info.get('holdings', {})
        if isinstance(holdings, dict) and 'countryWeightings' in holdings:
            countries = holdings['countryWeightings']
            print(f"Countries: {countries[:2]}... (total {len(countries)})")
        else:
            print("No country data")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 40)

if __name__ == "__main__":
    symbols = [
        "VUAA.DE", # Vanguard S&P 500 Accumulating ETF EUR
        "VWCE.DE", # Vanguard FTSE All-World Acc ETF EUR
        "0P00000XXD.F", # Example for mutual fund
        "IE00BYX5NX33.SG", # From PRD example
        "URTH"
    ]
    for s in symbols:
        test_yfinance(s)
