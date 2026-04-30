"""Portfolio models."""

from pydantic import BaseModel, Field


class InvestmentBase(BaseModel):
	"""Base investment model."""

	symbol: str = Field(..., min_length=1, max_length=20)
	name: str = Field(default="", max_length=200)
	quantity: float = Field(..., gt=0)
	purchase_price: float = Field(..., gt=0)
	purchase_date: str
	asset_type: str | None = Field(default="stock", max_length=50)
	currency: str | None = Field(default="USD", max_length=3)


class Investment(InvestmentBase):
	"""Investment model with additional fields."""

	id: int
	current_price: float | None = None
	resolved_symbol: str | None = None
	last_price_timestamp: str | None = None


class Portfolio(BaseModel):
	"""Portfolio model."""

	username: str
	holdings: list[Investment] = []


class PortfolioSummary(BaseModel):
	"""Portfolio summary with aggregated data."""

	total_investments: int
	total_cost: float
	total_value: float
	total_gain_loss: float
