"""
Test script to verify ISIN resolution using the static mapper.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.isin_mapper import get_isin_mapper
from app.services.finnhub import FinnhubService
from app.config import Settings


async def test_isin_resolution():
    """Test ISIN to ticker resolution and price fetching."""

    # Test ISINs
    test_isins = [
        "IE0032126645",  # Vanguard U.S. 500 -> VOO
        "IE00BYX5NX33",  # Fidelity MSCI World -> URTH
        "IE0031786696",  # Vanguard Emerging Markets -> VWO
    ]

    print("=" * 60)
    print("Testing ISIN Resolution and Price Fetching")
    print("=" * 60)

    # Get mapper
    isin_mapper = get_isin_mapper()

    # Test resolution
    print("\n1. Testing static ISIN mapping:")
    print("-" * 60)
    for isin in test_isins:
        ticker = isin_mapper.resolve_isin(isin)
        info = isin_mapper.get_mapping_info(isin)

        if ticker:
            print(f"\n  ISIN: {isin}")
            print(f"  --> Ticker: {ticker}")
            print(f"  --> Name: {info.get('name', 'N/A')}")
            print(f"  --> Exchange: {info.get('exchange', 'N/A')}")
            print(f"  --> Benchmark: {info.get('benchmark_index', 'N/A')}")
        else:
            print(f"\n  ISIN: {isin} -> No mapping found")

    # Test price fetching
    print("\n\n2. Testing price fetching:")
    print("-" * 60)

    fh = FinnhubService()
    for isin in test_isins:
        ticker = isin_mapper.resolve_isin(isin)
        if ticker:
            try:
                quote = await fh.get_quote(ticker)
                if quote:
                    current_price = quote.get("c", 0)
                    change = quote.get("d", 0)
                    change_pct = quote.get("dp", 0)

                    print(f"\n  {ticker}:")
                    print(f"    Price: ${current_price:.2f}")
                    print(f"    Change: ${change:.2f} ({change_pct:.2f}%)")
                else:
                    print(f"\n  {ticker}: No quote data available")
            except Exception as e:
                print(f"\n  {ticker}: Error - {e}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_isin_resolution())
