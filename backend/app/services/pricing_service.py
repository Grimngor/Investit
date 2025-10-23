"""Pricing service for retrieving market data and prices."""

from typing import Any

from app.services.finnhub import FinnhubService


class PricingService:
    """Service for fetching and managing market prices."""

    def __init__(self):
        """Initialize pricing service with Finnhub integration."""
        self.finnhub = FinnhubService()

    async def fetch_portfolio_data(self, symbols: list[str]) -> dict[str, Any]:
        """
        Fetch data for multiple symbols.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dictionary mapping symbols to their data
        """
        results = {}

        for symbol in symbols:
            quote = await self.finnhub.get_quote(symbol)
            if quote:
                results[symbol] = quote

        return results

    async def fetch_symbol_details(self, symbol: str) -> dict[str, Any] | None:
        """
        Fetch detailed information for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with symbol details or None
        """
        profile = await self.finnhub.get_company_profile(symbol)
        quote = await self.finnhub.get_quote(symbol)

        if not profile and not quote:
            return None

        return {"symbol": symbol, "profile": profile, "quote": quote}
