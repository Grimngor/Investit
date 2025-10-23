"""Finnhub API service for fetching stock market data."""

import aiohttp
from typing import Optional, Dict, Any, List
from cachetools import TTLCache
from app.config import settings


class FinnhubService:
    """Service for interacting with Finnhub API."""

    def __init__(self):
        """Initialize Finnhub service with API key and caches."""
        self.api_key = settings.FINNHUB_API_KEY
        self.base_url = "https://finnhub.io/api/v1"

        # Initialize TTL caches
        self._quote_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes
        self._profile_cache = TTLCache(maxsize=500, ttl=600)  # 10 minutes
        self._symbols_cache = TTLCache(maxsize=100, ttl=7200)  # 2 hours

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with quote data or None if not found
        """
        if not symbol:
            return None

        # Check cache first
        if symbol in self._quote_cache:
            return self._quote_cache[symbol]

        try:
            async with aiohttp.ClientSession() as session:
                params = {"symbol": symbol, "token": self.api_key.strip()}
                async with session.get(f"{self.base_url}/quote", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Cache the result
                        self._quote_cache[symbol] = data
                        return data
                    elif response.status == 401:
                        print(f"Finnhub API authentication failed (status 401). Check API key: {self.api_key[:10]}...")
                        return None
                    elif response.status == 403:
                        print(f"Finnhub API forbidden (status 403) for symbol {symbol}. Free tier may not support this symbol.")
                        return None
                    else:
                        print(f"Finnhub API error for {symbol}: {response.status}")
                        return None
        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            return None

    async def search_symbol(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for symbols matching query.

        Args:
            query: Search query string

        Returns:
            List of matching symbols
        """
        if not query:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                params = {"q": query, "token": self.api_key.strip()}
                async with session.get(f"{self.base_url}/search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", [])
                    else:
                        print(f"Finnhub search error: {response.status}")
                        return []
        except Exception as e:
            print(f"Error searching for {query}: {e}")
            return []

    async def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company profile for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with company profile or None
        """
        if not symbol:
            return None

        # Check cache
        if symbol in self._profile_cache:
            return self._profile_cache[symbol]

        try:
            async with aiohttp.ClientSession() as session:
                params = {"symbol": symbol, "token": self.api_key.strip()}
                async with session.get(f"{self.base_url}/stock/profile2", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._profile_cache[symbol] = data
                        return data
                    else:
                        return None
        except Exception as e:
            print(f"Error fetching profile for {symbol}: {e}")
            return None
