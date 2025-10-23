"""Portfolio router for managing investment portfolios."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional, Tuple
import datetime
from app.models.portfolio import Portfolio, Investment, InvestmentCreate, InvestmentUpdate, PortfolioSummary
from app.models.user import User
from app.services.auth import get_current_user
from app.services.finnhub import FinnhubService
from app.services.isin_mapper import get_isin_mapper
from app.models.persistence import save_user_data, load_user_data, get_all_users

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

# Module-level throttle tracking
_LAST_PORTFOLIO_FETCH: Dict[str, datetime.datetime] = {}
_THROTTLE_SECONDS = 30


def _should_refresh_prices(username: str) -> bool:
    """Check if enough time has passed since last price refresh."""
    now = datetime.datetime.now()
    last_fetch = _LAST_PORTFOLIO_FETCH.get(username)

    if last_fetch is None:
        return True

    elapsed = (now - last_fetch).total_seconds()
    return elapsed >= _THROTTLE_SECONDS


async def get_current_price_for_symbol(original_symbol: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Get current price for a symbol, resolving ISIN if needed.

    Args:
        original_symbol: The symbol or ISIN to get price for

    Returns:
        Tuple of (price, resolved_symbol) or (None, None) if not found
    """
    finnhub_service = FinnhubService()
    isin_mapper = get_isin_mapper()

    # Check if it's an ISIN (12 characters, starts with 2 letters)
    is_isin = len(original_symbol) == 12 and original_symbol[:2].isalpha()

    if is_isin:
        # Try to resolve ISIN to ticker
        ticker = isin_mapper.resolve_isin(original_symbol)
        if ticker:
            quote = await finnhub_service.get_quote(ticker)
            if quote and quote.get("c"):
                return quote["c"], ticker
        return None, None
    else:
        # Direct ticker lookup
        quote = await finnhub_service.get_quote(original_symbol)
        if quote and quote.get("c"):
            return quote["c"], original_symbol
        return None, None


@router.get("/", response_model=Portfolio)
async def get_portfolio(current_user: User = Depends(get_current_user)):
    """Get the current user's portfolio with live prices."""
    users = get_all_users()
    user_data = users.get(current_user.username)

    if not user_data:
        return Portfolio(username=current_user.username, holdings=[])

    holdings = user_data.get("holdings", [])

    # Check if we should refresh prices
    should_refresh = _should_refresh_prices(current_user.username)

    if should_refresh and holdings:
        # Get unique symbols
        symbols = list(set(h.get("symbol") for h in holdings if h.get("symbol")))
        print(f"Refreshing current prices for {len(symbols)} symbols: {symbols}")

        # Fetch prices for each symbol
        symbol_prices: Dict[str, Tuple[Optional[float], Optional[str]]] = {}
        for symbol in symbols:
            price, resolved_symbol = await get_current_price_for_symbol(symbol)
            if price:
                symbol_prices[symbol] = (price, resolved_symbol)

        # Update holdings with new prices
        now_iso = datetime.datetime.now().isoformat()
        for holding in holdings:
            symbol = holding.get("symbol")
            if symbol in symbol_prices:
                price, resolved_symbol = symbol_prices[symbol]
                holding["current_price"] = price
                holding["last_price_timestamp"] = now_iso
                holding["resolved_symbol"] = resolved_symbol

        # Save updated prices
        save_user_data(current_user.username, {"holdings": holdings})

        # Update throttle timestamp
        _LAST_PORTFOLIO_FETCH[current_user.username] = datetime.datetime.now()
    else:
        if holdings:
            print(f"Skipping price refresh (throttled) for {current_user.username}")

    # Convert holdings to Investment objects
    investments = []
    for h in holdings:
        investments.append(
            Investment(
                id=h.get("id"),
                symbol=h.get("symbol"),
                name=h.get("name", ""),
                quantity=h.get("quantity", 0),
                purchase_price=h.get("purchase_price", 0),
                purchase_date=h.get("purchase_date"),
                current_price=h.get("current_price"),
                asset_type=h.get("asset_type", "stock"),
                currency=h.get("currency", "USD"),
                resolved_symbol=h.get("resolved_symbol"),
                last_price_timestamp=h.get("last_price_timestamp"),
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
        "last_price_timestamp": datetime.datetime.now().isoformat() if current_price else None,
    }

    holdings.append(new_investment)
    user_data["holdings"] = holdings
    save_user_data(current_user.username, user_data)

    return Investment(**new_investment)


@router.put("/{investment_id}", response_model=Investment)
async def update_investment(investment_id: int, investment: InvestmentUpdate, current_user: User = Depends(get_current_user)):
    """Update an existing investment."""
    users = get_all_users()
    user_data = users.get(current_user.username, {})
    holdings = user_data.get("holdings", [])

    # Find the investment
    holding = next((h for h in holdings if h.get("id") == investment_id), None)
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found")

    # Update fields
    update_data = investment.dict(exclude_unset=True)
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

    return None


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(current_user: User = Depends(get_current_user)):
    """Get portfolio summary with totals and performance."""
    portfolio = await get_portfolio(current_user)

    total_cost = sum(h.quantity * h.purchase_price for h in portfolio.holdings)
    total_value = sum(h.quantity * (h.current_price or h.purchase_price) for h in portfolio.holdings)
    total_gain_loss = total_value - total_cost

    return PortfolioSummary(
        total_investments=len(portfolio.holdings), total_cost=total_cost, total_value=total_value, total_gain_loss=total_gain_loss
    )
