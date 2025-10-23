"""Debug router for API testing and diagnostics."""

from fastapi import APIRouter

from app.config import settings
from app.services.finnhub import FinnhubService

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/finnhub-check")
async def check_finnhub():
    """Check Finnhub API connectivity and authentication."""
    finnhub = FinnhubService()

    # Test with a known symbol
    result = await finnhub.search_symbol("AAPL")

    return {
        "status": "ok" if result else "error",
        "api_key_length": len(settings.FINNHUB_API_KEY),
        "result_count": len(result) if result else 0,
        "sample": result[0] if result else None,
    }


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Test quote fetching for a specific symbol."""
    finnhub = FinnhubService()
    quote = await finnhub.get_quote(symbol)

    if quote:
        return {"status": "ok", "symbol": symbol, "quote": quote}
    else:
        return {"status": "error", "symbol": symbol, "message": "Quote not found or API error"}
