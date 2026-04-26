"""Validation utilities for orders, ISINs, and other data."""

import re
from datetime import datetime
from typing import Any

ISIN_LENGTH = 12
MAX_SYMBOL_LENGTH = 20
CURRENCY_CODE_LENGTH = 3
CRYPTO_MIN_LEN = 3
CRYPTO_MAX_LEN = 5


def validate_isin(isin: str) -> bool:
	"""
	Validate ISIN format.

	ISIN structure: 2 letters (country) + 9 alphanumeric + 1 check digit
	Total: 12 characters

	Args:
		isin: ISIN code to validate

	Returns:
		True if valid, False otherwise
	"""
	if not isin or len(isin) != ISIN_LENGTH:
		return False

	# First two characters must be letters (country code)
	if not isin[:2].isalpha():
		return False

	# Last 10 characters must be alphanumeric
	return isin[2:].isalnum()


def validate_date(date_str: str, date_format: str = "%Y-%m-%d") -> bool:
	"""
	Validate date string format.

	Args:
		date_str: Date string to validate
		date_format: Expected date format (default: YYYY-MM-DD)

	Returns:
		True if valid, False otherwise
	"""
	try:
		datetime.strptime(date_str, date_format)
		return True
	except (ValueError, TypeError):
		return False


def validate_price(price: Any) -> bool:
	"""
	Validate market price.

	Args:
		price: Price to validate

	Returns:
		True if valid (positive number and not ridiculously high), False otherwise
	"""
	try:
		if not isinstance(price, int | float):
			price = float(price)

		# Price must be positive
		if price <= 0:
			return False

		# Threshold for "crazy" prices (sanity check)
		# 10 million per share/unit is a reasonable upper bound for now
		if price > 10_000_000:
			return False

		return True
	except (ValueError, TypeError):
		return False


def validate_amount(amount: float) -> bool:
	"""
	Validate monetary amount.

	Args:
		amount: Amount to validate

	Returns:
		True if valid (positive number), False otherwise
	"""
	try:
		return isinstance(amount, int | float) and amount > 0
	except (ValueError, TypeError):
		return False


def validate_shares(shares: float) -> bool:
	"""
	Validate number of shares.

	Args:
		shares: Number of shares to validate

	Returns:
		True if valid (positive number), False otherwise
	"""
	try:
		return isinstance(shares, int | float) and shares > 0
	except (ValueError, TypeError):
		return False


def validate_order_type(order_type: str) -> bool:
	"""
	Validate order type.

	Args:
		order_type: Order type to validate ('buy' or 'sell')

	Returns:
		True if valid, False otherwise
	"""
	return order_type.lower() in ["buy", "sell"]


def validate_order(order: dict[str, Any]) -> tuple[bool, list[str]]:
	"""
	Validate a complete order dictionary.

	Args:
		order: Order dictionary to validate

	Returns:
		Tuple of (is_valid, error_messages)
	"""
	errors = []

	# Required fields
	required_fields = ["date", "isin", "amount_eur", "shares", "order_type"]
	for field in required_fields:
		if field not in order:
			errors.append(f"Missing required field: {field}")

	if errors:
		return False, errors

	# Validate date
	if not validate_date(order["date"]):
		errors.append(f"Invalid date format: {order['date']} (expected YYYY-MM-DD)")

	# Validate ISIN
	if not validate_isin(order["isin"]):
		errors.append(f"Invalid ISIN: {order['isin']} (expected 12 characters, 2 letters + 10 alphanumeric)")

	# Validate amount
	if not validate_amount(order["amount_eur"]):
		errors.append(f"Invalid amount: {order['amount_eur']} (must be positive)")

	# Validate shares
	if not validate_shares(order["shares"]):
		errors.append(f"Invalid shares: {order['shares']} (must be positive)")

	# Validate order type
	if not validate_order_type(order["order_type"]):
		errors.append(f"Invalid order_type: {order['order_type']} (must be 'buy' or 'sell')")

	return len(errors) == 0, errors


def validate_symbol(symbol: str) -> bool:
	"""
	Validate ticker symbol format.

	Args:
		symbol: Ticker symbol to validate

	Returns:
		True if valid, False otherwise
	"""
	if not symbol or len(symbol) > MAX_SYMBOL_LENGTH:
		return False
	# Allow alphanumeric, dots, and hyphens
	return bool(re.match(r"^[A-Z0-9.-]+$", symbol.upper()))


def is_crypto_symbol(identifier: str) -> bool:
	"""Return True if identifier looks like a cryptocurrency symbol (e.g., BTC, ETH).

	Rules (heuristic):
	- Length between 3 and 5 characters
	- All uppercase letters
	- Not a valid ISIN (to avoid clashes when user enters an ISIN)

	Args:
		identifier: Potential crypto symbol

	Returns:
		True if matches crypto symbol pattern, otherwise False
	"""
	if not identifier:
		return False
	identifier = identifier.strip().upper()
	# Exclude valid ISINs
	if validate_isin(identifier):
		return False
	if not (CRYPTO_MIN_LEN <= len(identifier) <= CRYPTO_MAX_LEN and identifier.isalpha() and identifier.isupper()):
		return False

	# Exclude a small set of well-known equity tickers (heuristic)
	exclusions = {"AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "META", "NVDA"}
	return identifier not in exclusions


def get_crypto_yfinance_symbol(crypto_symbol: str, currency: str = "EUR") -> str:
	"""Convert a raw crypto symbol (BTC) to yfinance pair symbol (BTC-EUR).

	Args:
		crypto_symbol: Base crypto symbol (e.g., 'BTC')
		currency: Fiat currency code (default EUR)

	Returns:
		Yahoo Finance formatted symbol (e.g., 'BTC-EUR')
	"""
	return f"{crypto_symbol.strip().upper()}-{currency.strip().upper()}"


def validate_currency(currency: str) -> bool:
	"""
	Validate currency code (ISO 4217).

	Args:
		currency: Currency code to validate (e.g., 'USD', 'EUR')

	Returns:
		True if valid, False otherwise
	"""
	if not currency or len(currency) != CURRENCY_CODE_LENGTH:
		return False

	return currency.upper().isalpha()


def sanitize_string(value: str, max_length: int | None = None) -> str:
	"""
	Sanitize string input.

	Args:
		value: String to sanitize
		max_length: Maximum allowed length (optional)

	Returns:
		Sanitized string
	"""
	if not isinstance(value, str):
		value = str(value)

	# Strip whitespace
	value = value.strip()

	# Limit length if specified
	if max_length and len(value) > max_length:
		value = value[:max_length]

	return value
