"""Portfolio router for managing investment portfolios."""

from fastapi import APIRouter, Depends

from app.models.portfolio import (
	Portfolio,
	PortfolioSummary,
)
from app.models.user import User
from app.services.auth import get_current_user
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/", response_model=Portfolio)
async def get_portfolio(current_user: User = Depends(get_current_user)) -> Portfolio:
	"""Get the current user's portfolio computed from orders."""
	return PortfolioService.get_portfolio(current_user.username)


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(current_user: User = Depends(get_current_user)) -> PortfolioSummary:
	"""Get portfolio summary with totals and performance."""
	return PortfolioService.get_summary(current_user.username)
