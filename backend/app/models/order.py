"""Order and related models for the investment tracking system."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class Order(BaseModel):
    """
    Represents a buy/sell order for an investment instrument.

    Based on PRD Section 3: Order-based data model.
    """

    id: Optional[str] = None
    date: str = Field(..., description="Order execution date in YYYY-MM-DD format")
    isin: str = Field(..., min_length=12, max_length=12, description="ISIN code (12 characters)")
    ticker: Optional[str] = Field(None, description="Optional ticker symbol")
    amount_eur: float = Field(..., gt=0, description="Order amount in EUR")
    shares: float = Field(..., gt=0, description="Number of shares/units")
    order_type: str = Field("buy", description="Order type: buy or sell")
    status: str = Field("Finalizada", description="Order status: Finalizada or Rechazada")
    notes: str = Field("", description="Optional notes")
    created_at: Optional[str] = None


class OrderCreate(BaseModel):
    """Schema for creating a new order manually."""

    date: str
    isin: str = Field(..., min_length=12, max_length=12)
    ticker: Optional[str] = None
    amount_eur: float = Field(..., gt=0)
    shares: float = Field(..., gt=0)
    order_type: str = "buy"
    status: str = "Finalizada"
    notes: str = ""


class OrderUpdate(BaseModel):
    """Schema for updating an existing order."""

    date: Optional[str] = None
    isin: Optional[str] = None
    ticker: Optional[str] = None
    amount_eur: Optional[float] = None
    shares: Optional[float] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Response schema for order operations."""

    id: str
    date: str
    isin: str
    ticker: Optional[str]
    amount_eur: float
    shares: float
    order_type: str
    status: str
    notes: str
    created_at: str


class Instrument(BaseModel):
    """
    Represents an investment instrument (ETF, fund, stock).

    Separate from orders per PRD architecture.
    """

    isin: str = Field(..., min_length=12, max_length=12)
    ticker: str
    name: str
    instrument_type: str = Field(..., description="ETF, Index Fund, Stock, Bond")
    currency: str = "EUR"
    sector: Optional[str] = None
    region: Optional[str] = None
    geography: Optional[str] = None
    risk_rating: Optional[str] = None


class Price(BaseModel):
    """
    Current price for an instrument.

    Separate collection per PRD.
    """

    isin: str
    ticker: str
    price: float
    currency: str = "EUR"
    timestamp: str
    source: str = "finnhub"


class UserSettings(BaseModel):
    """User-specific settings."""

    username: str
    default_currency: str = "EUR"
    theme: str = "light"
    notifications_enabled: bool = True
