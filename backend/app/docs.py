"""FastAPI documentation configuration."""

tags_metadata = [
	{
		"name": "auth",
		"description": "Authentication and user management operations. Register, login, and manage user tokens.",
	},
	{
		"name": "portfolio",
		"description": "Portfolio views computed from persisted orders.",
	},
	{
		"name": "orders",
		"description": "Order import and CRUD operations.",
	},
	{
		"name": "prices",
		"description": "Price refresh and cache status operations.",
	},
	{
		"name": "dashboard",
		"description": "Dashboard KPIs, time series, allocations, and price status.",
	},
	{
		"name": "instruments",
		"description": "Instrument metadata and allocation overrides.",
	},
	{
		"name": "gmail",
		"description": "Gmail-backed MyInvestor order import connection, scan, and import operations.",
	},
	{
		"name": "websocket",
		"description": "WebSocket connections for real-time updates.",
	},
	{
		"name": "debug",
		"description": "Debug and diagnostic endpoints for development and testing.",
	},
]

description = """
**Investit API** allows you to manage your investment portfolio with real-time market data.

## Features

* **Authentication**: Secure JWT-based authentication system
* **Portfolio Management**: Track funds, ETFs, stocks, and crypto from order history
* **Price Refresh**: Yahoo Finance-backed price and metadata refreshes
* **Instrument Metadata**: Manual overrides and provider-enriched allocations
* **WebSocket**: Real-time updates and notifications

## Getting Started

1. Register a new user account
2. Login to receive an access token
3. Use the token to access portfolio endpoints
4. Add investments and track performance

"""
