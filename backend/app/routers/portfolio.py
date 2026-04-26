"""Portfolio router for managing investment portfolios."""

import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.persistence import get_all_users, save_user_data
from app.models.portfolio import (
	Investment,
	InvestmentCreate,
	InvestmentUpdate,
	Portfolio,
	PortfolioSummary,
)
from app.models.user import User
from app.services.auth import get_current_user
from app.services.compute_service import ComputeService
from app.services.isin_mapper import get_isin_mapper
from app.services.yahoo_finance import YahooFinanceService

ISIN_LENGTH = 12

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

# Module-level throttle tracking
_LAST_PORTFOLIO_FETCH: dict[str, datetime.datetime] = {}
_THROTTLE_SECONDS = 30


def _should_refresh_prices(username: str) -> bool:
	"""Check if enough time has passed since last price refresh."""
	now = datetime.datetime.now()
	last_fetch = _LAST_PORTFOLIO_FETCH.get(username)

	if last_fetch is None:
		return True

	elapsed = (now - last_fetch).total_seconds()
	return elapsed >= _THROTTLE_SECONDS


async def get_current_price_for_symbol(
	original_symbol: str,
) -> tuple[float | None, str | None]:
	"""
	Get current price for a symbol, resolving ISIN if needed.

	Args:
		original_symbol: The symbol or ISIN to get price for

	Returns:
		Tuple of (price, resolved_symbol) or (None, None) if not found
	"""
	# Removed finnhub reference
	isin_mapper = get_isin_mapper()
	yahoo_finance = YahooFinanceService()

	# Check if it's an ISIN (12 characters, starts with 2 letters)
	is_isin = len(original_symbol) == ISIN_LENGTH and original_symbol[:2].isalpha()

	if is_isin:
		# Try to resolve ISIN to ticker
		ticker = isin_mapper.resolve_isin(original_symbol)
		if ticker:
			quote = await yahoo_finance.get_quote(ticker)
			if quote and quote.get("price"):
				return quote["price"], ticker
		return None, None
	else:
		# Direct ticker lookup
		quote = await yahoo_finance.get_quote(original_symbol)
		if quote and quote.get("price"):
			return quote["price"], original_symbol
		return None, None


@router.get("/", response_model=Portfolio)
async def get_portfolio(current_user: User = Depends(get_current_user)):
	"""Get the current user's portfolio computed from orders."""
	users = get_all_users()
	user_data = users.get(current_user.username)

	if not user_data:
		return Portfolio(username=current_user.username, holdings=[])

	# Get orders instead of holdings
	orders = user_data.get("orders", [])
	prices = user_data.get("prices", {})

	if not orders:
		return Portfolio(username=current_user.username, holdings=[])

	# Filter finalized orders
	finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]

	# Get unique ISINs
	unique_isins = set(o.get("isin") for o in finalized_orders if o.get("isin"))

	# Build investments from computed positions
	investments = []
	for isin in unique_isins:
		position = ComputeService.calculate_position(finalized_orders, isin)

		if position["total_shares"] > 0:
			# Get price for this ISIN
			price_data = prices.get(isin, {})
			current_price = price_data.get("price")
			last_price_timestamp = price_data.get("timestamp")

			# Get the most recent order for this ISIN to extract metadata
			isin_orders = [o for o in finalized_orders if o.get("isin") == isin]
			latest_order = max(isin_orders, key=lambda x: x.get("date", ""))

			investments.append(
				Investment(
					id=len(investments) + 1,  # Generate sequential ID
					symbol=isin,  # Use ISIN as symbol
					name=price_data.get("name", isin),  # Use name from prices or fallback to ISIN
					quantity=position["total_shares"],
					purchase_price=position["average_cost"],
					purchase_date=latest_order.get("date", ""),
					current_price=current_price,
					asset_type="stock",
					currency="EUR",
					resolved_symbol=None,
					last_price_timestamp=last_price_timestamp,
				)
			)

	return Portfolio(username=current_user.username, holdings=investments)


@router.post("/", response_model=Investment, status_code=status.HTTP_201_CREATED)
async def add_investment(investment: InvestmentCreate, current_user: User = Depends(get_current_user)):
	"""Add a new investment to the portfolio."""
	users = get_all_users()
	user_data = users.get(current_user.username, {})
	holdings = user_data.get("holdings", [])

	# Generate new ID
	max_id = max([h.get("id", 0) for h in holdings], default=0)
	new_id = max_id + 1

	# Get current price
	current_price, resolved_symbol = await get_current_price_for_symbol(investment.symbol)

	new_investment = {
		"id": new_id,
		"symbol": investment.symbol,
		"name": investment.name or "",
		"quantity": investment.quantity,
		"purchase_price": investment.purchase_price,
		"purchase_date": investment.purchase_date,
		"current_price": current_price,
		"asset_type": investment.asset_type or "stock",
		"currency": investment.currency or "USD",
		"resolved_symbol": resolved_symbol,
		"last_price_timestamp": (datetime.datetime.now().isoformat() if current_price else None),
	}

	holdings.append(new_investment)
	user_data["holdings"] = holdings
	save_user_data(current_user.username, user_data)

	return Investment(**new_investment)


@router.put("/{investment_id}", response_model=Investment)
async def update_investment(
	investment_id: int,
	investment: InvestmentUpdate,
	current_user: User = Depends(get_current_user),
):
	"""Update an existing investment."""
	users = get_all_users()
	user_data = users.get(current_user.username, {})
	holdings = user_data.get("holdings", [])

	# Find the investment
	holding = next((h for h in holdings if h.get("id") == investment_id), None)
	if not holding:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found")

	# Update fields
	update_data = investment.model_dump(exclude_unset=True)
	holding.update(update_data)

	# Refresh price if symbol changed
	if "symbol" in update_data:
		current_price, resolved_symbol = await get_current_price_for_symbol(holding["symbol"])
		holding["current_price"] = current_price
		holding["resolved_symbol"] = resolved_symbol
		holding["last_price_timestamp"] = datetime.datetime.now().isoformat() if current_price else None

	save_user_data(current_user.username, user_data)

	return Investment(**holding)


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_investment(investment_id: int, current_user: User = Depends(get_current_user)):
	"""Delete an investment from the portfolio."""
	users = get_all_users()
	user_data = users.get(current_user.username, {})
	holdings = user_data.get("holdings", [])

	# Find and remove the investment
	initial_count = len(holdings)
	holdings = [h for h in holdings if h.get("id") != investment_id]

	if len(holdings) == initial_count:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found")

	user_data["holdings"] = holdings
	save_user_data(current_user.username, user_data)


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(current_user: User = Depends(get_current_user)):
	"""Get portfolio summary with totals and performance."""
	portfolio = await get_portfolio(current_user)

	total_cost = sum(h.quantity * h.purchase_price for h in portfolio.holdings)
	total_value = sum(h.quantity * (h.current_price or h.purchase_price) for h in portfolio.holdings)
	total_gain_loss = total_value - total_cost

	return PortfolioSummary(
		total_investments=len(portfolio.holdings),
		total_cost=total_cost,
		total_value=total_value,
		total_gain_loss=total_gain_loss,
	)
