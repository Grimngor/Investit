"""FastAPI documentation configuration."""

tags_metadata = [
    {
        "name": "auth",
        "description": "Authentication and user management operations. Register, login, and manage user tokens.",
    },
    {
        "name": "portfolio",
        "description": "Portfolio management operations. Create, read, update, and delete investments in your portfolio.",
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
* **Portfolio Management**: Track stocks, ETFs, and mutual funds
* **Real-time Prices**: Integration with Finnhub API for live market data
* **ISIN Resolution**: Automatic mapping of European fund ISINs to tradable proxies
* **WebSocket**: Real-time updates and notifications

## Getting Started

1. Register a new user account
2. Login to receive an access token
3. Use the token to access portfolio endpoints
4. Add investments and track performance

"""
