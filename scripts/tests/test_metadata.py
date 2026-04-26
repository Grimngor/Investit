import sys
import asyncio
try:
    import mstarpy
    from yahooquery import Ticker
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def test_all():
    isins = ["IE00BYX5NX33", "IE0032126645", "IE0031786696"]

    print("--- Testing mstarpy ---")
    for isin in isins:
        try:
            fund = mstarpy.Funds(isin, language="en-gb")
            print(f"{isin} ({fund.name}):")
            print(f"  Regional keys: {list(fund.regionalSector.keys()) if hasattr(fund, 'regionalSector') else 'None'}")
            print(f"  Sector keys: {list(fund.sector.keys()) if hasattr(fund, 'sector') else 'None'}")
        except Exception as e:
            print(f"  mstarpy Error for {isin}: {e}")

    tickers = ["VOO", "URTH", "VWO", "IE00BYX5NX33.SG", "VUAA.DE"]
    print("\n--- Testing yahooquery ---")
    for tk in tickers:
        try:
            t = Ticker(tk)
            print(f"{tk}:")
            sw = t.fund_sector_weightings
            print(f"  Sector weighting type: {type(sw)}")
            if hasattr(sw, 'to_dict'):
                print(f"  Sector keys: {list(sw.to_dict().keys())[:3]}")

            phi = t.fund_holding_info
            print(f"  Holding info keys: {list(phi.keys()) if isinstance(phi, dict) else type(phi)}")
        except Exception as e:
            print(f"  yahooquery Error for {tk}: {e}")

if __name__ == "__main__":
    asyncio.run(test_all())
