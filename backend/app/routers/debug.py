"""Debug router for API testing and diagnostics."""

from fastapi import APIRouter

from app.services.yahoo_finance import YahooFinanceService

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/yahoo-check")
async def check_yahoo():
	"""Check Yahoo Finance connectivity."""
	yahoo = YahooFinanceService()

	# Test with a known symbol
	quote = await yahoo.get_quote("AAPL")

	return {
		"status": "ok" if quote else "error",
		"quote": quote if quote else None,
	}


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
	"""Test quote fetching for a specific symbol."""
	yahoo = YahooFinanceService()
	quote = await yahoo.get_quote(symbol)

	if quote:
		return {"status": "ok", "symbol": symbol, "quote": quote}
	else:
		return {"status": "error", "symbol": symbol, "message": "Quote not found or API error"}
