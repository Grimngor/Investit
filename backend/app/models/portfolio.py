"""Portfolio models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class InvestmentBase(BaseModel):
    """Base investment model."""

    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(default="", max_length=200)
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)
    purchase_date: str
    asset_type: Optional[str] = Field(default="stock", max_length=50)
    currency: Optional[str] = Field(default="USD", max_length=3)


class InvestmentCreate(InvestmentBase):
    """Investment creation model."""

    pass


class InvestmentUpdate(BaseModel):
    """Investment update model."""

    symbol: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, max_length=200)
    quantity: Optional[float] = Field(None, gt=0)
    purchase_price: Optional[float] = Field(None, gt=0)
    purchase_date: Optional[str] = None
    asset_type: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=3)


class Investment(InvestmentBase):
    """Investment model with additional fields."""

    id: int
    current_price: Optional[float] = None
    resolved_symbol: Optional[str] = None
    last_price_timestamp: Optional[str] = None


class Portfolio(BaseModel):
    """Portfolio model."""

    username: str
    holdings: List[Investment] = []


class PortfolioSummary(BaseModel):
    """Portfolio summary with aggregated data."""

    total_investments: int
    total_cost: float
    total_value: float
    total_gain_loss: float
