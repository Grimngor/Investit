"""CSV parser for Spanish bank format order imports."""

import csv
import logging
import re
import uuid
from datetime import datetime
from io import StringIO
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class CSVParseError(Exception):
	"""Custom exception for CSV parsing errors."""

	pass


class SpanishOrderCSVParser:
	"""
	Parser for Spanish bank CSV format.

	Expected CSV format per PRD:
	- Delimiter: Automatically detects comma (,) or semicolon (;) delimiters
	- Headers: Fecha de la orden, ISIN, Importe estimado, Nº de participaciones, Estado
	- Date format: DD/MM/YYYY
	- Amount format: can use ',' or '.' as decimal separator, may include ' EUR' suffix
	- Estado: 'Finalizada' (accept), 'Rechazada' (skip)
	- Note: Header 'Nº' may appear as 'NÂº' due to encoding issues
	"""

	EXPECTED_HEADERS: ClassVar[list[str]] = [
		"Fecha de la orden",
		"ISIN",
		"Importe neto",  # Changed from "Importe estimado" - use actual net amount
		"Nº de participaciones",
		"Estado",
	]

	# Alternative headers to check (fallback if main headers not found)
	ALTERNATIVE_AMOUNT_HEADERS: ClassVar[list[str]] = [
		"Importe neto",
		"Importe estimado",
		"Importe",
	]

	HEADER_VARIATIONS: ClassVar[dict[str, list[str]]] = {
		"Nº de participaciones": ["Nº de participaciones", "NÂº de participaciones", "N° de participaciones"],
		"Importe neto": ["Importe neto", "Importe estimado", "Importe"],
	}

	ISIN_LENGTH: ClassVar[int] = 12

	def __init__(self, encoding: str = "utf-8"):
		"""Initialize parser with encoding."""
		self.encoding = encoding

	def _normalize_header(self, header: str) -> str:
		"""Normalize header name to handle encoding variations."""
		header = header.strip()
		for normalized, variations in self.HEADER_VARIATIONS.items():
			if header in variations:
				return normalized
		return header

	def _parse_date(self, date_str: str, row_num: int) -> str:
		"""
		Parse date from DD/MM/YYYY to YYYY-MM-DD format.

		Args:
			date_str: Date string in DD/MM/YYYY format
			row_num: Row number for error reporting

		Returns:
			Date string in YYYY-MM-DD format

		Raises:
			CSVParseError: If date format is invalid
		"""
		date_str = date_str.strip()
		try:
			dt = datetime.strptime(date_str, "%d/%m/%Y")
			return dt.strftime("%Y-%m-%d")
		except ValueError as exc:
			raise CSVParseError(f"Row {row_num}: Invalid date format '{date_str}'. Expected DD/MM/YYYY") from exc

	def _parse_amount(self, amount_str: str, row_num: int) -> float:
		"""
		Parse amount, handling Spanish format (comma as decimal separator).

		Args:
			amount_str: Amount string (e.g., '1.234,56' or '1234.56' or '1234,56 EUR')
			row_num: Row number for error reporting

		Returns:
			Amount as float

		Raises:
			CSVParseError: If amount format is invalid
		"""
		amount_str = amount_str.strip()

		# Remove EUR suffix if present
		amount_str = re.sub(r"\s*EUR\s*$", "", amount_str, flags=re.IGNORECASE)

		# Detect format based on presence and position of comma/dot
		has_comma = "," in amount_str
		has_dot = "." in amount_str

		if has_comma and has_dot:
			# Both present - determine which is decimal separator
			last_comma_pos = amount_str.rfind(",")
			last_dot_pos = amount_str.rfind(".")

			# Spanish format: 1.234,56 (dot thousands, comma decimal) vs US 1,234.56
			amount_str = amount_str.replace(".", "").replace(",", ".") if last_comma_pos > last_dot_pos else amount_str.replace(",", "")
		elif has_comma:
			# Only comma - assume it's decimal separator (Spanish format)
			amount_str = amount_str.replace(",", ".")
		# If only dot or neither, keep as is

		try:
			return float(amount_str)
		except ValueError as exc:
			raise CSVParseError(f"Row {row_num}: Invalid amount format '{amount_str}'") from exc

	def _parse_shares(self, shares_str: str, row_num: int) -> float:
		"""
		Parse number of shares.

		Args:
			shares_str: Shares string
			row_num: Row number for error reporting

		Returns:
			Shares as float (absolute value)

		Raises:
			CSVParseError: If shares format is invalid
		"""
		shares_str = shares_str.strip()

		# Handle comma as decimal separator
		shares_str = shares_str.replace(",", ".")

		try:
			shares = float(shares_str)
			# Return absolute value - sign is determined by amount field
			return abs(shares)
		except ValueError as exc:
			raise CSVParseError(f"Row {row_num}: Invalid shares format '{shares_str}'") from exc

	def parse_csv(self, csv_content: str) -> tuple[list[dict[str, Any]], list[str]]:
		"""
		Parse CSV content and return orders and errors.

		Args:
			csv_content: CSV file content as string

		Returns:
			Tuple of (parsed_orders, errors)
			- parsed_orders: List of order dictionaries
			- errors: List of error messages

		Order dictionary structure:
			{
				'date': 'YYYY-MM-DD',
				'isin': 'IE00BYX5NX33',
				'amount_eur': 300.00,
				'shares': 24.624,
				'order_type': 'buy' or 'sell',
				'status': 'Finalizada',
				'notes': ''
			}
		"""
		orders = []
		errors = []

		try:
			# Detect delimiter (semicolon or comma)
			first_line = csv_content.split("\n")[0] if csv_content else ""
			delimiter = ";" if ";" in first_line else ","

			# Parse CSV
			csv_file = StringIO(csv_content)
			reader = csv.DictReader(csv_file, delimiter=delimiter)

			# Normalize headers
			fieldnames = reader.fieldnames
			if fieldnames:
				reader.fieldnames = [self._normalize_header(h) for h in fieldnames]

			# Validate headers
			missing_headers = set(self.EXPECTED_HEADERS) - set(reader.fieldnames or [])
			if missing_headers:
				errors.append(f"Missing required headers: {', '.join(missing_headers)}")
				return orders, errors

			# Parse each row
			for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
				try:
					# Skip rejected orders
					estado = row.get("Estado", "").strip()
					if estado.lower() == "rechazada":
						continue

					# Parse date
					date_str = row.get("Fecha de la orden", "").strip()
					if not date_str:
						errors.append(f"Row {row_num}: Missing date")
						continue
					parsed_date = self._parse_date(date_str, row_num)

					# Parse ISIN
					isin = row.get("ISIN", "").strip()
					if not isin:
						errors.append(f"Row {row_num}: Missing ISIN")
						continue
					if len(isin) != self.ISIN_LENGTH:
						errors.append(f"Row {row_num}: Invalid ISIN length '{isin}' (expected 12 characters)")
						continue

					# Parse amount
					amount_str = row.get("Importe neto", "").strip()
					if not amount_str:
						errors.append(f"Row {row_num}: Missing amount")
						continue
					amount = self._parse_amount(amount_str, row_num)

					# Determine order type from amount sign
					order_type = "sell" if amount < 0 else "buy"
					amount_eur = abs(amount)

					# Parse shares
					shares_str = row.get("Nº de participaciones", "").strip()
					if not shares_str:
						errors.append(f"Row {row_num}: Missing shares")
						continue
					shares = self._parse_shares(shares_str, row_num)

					# Create order
					order = {
						"id": str(uuid.uuid4()),
						"date": parsed_date,
						"isin": isin,
						"amount_eur": amount_eur,
						"shares": shares,
						"order_type": order_type,
						"status": estado or "Finalizada",
						"notes": "",
						"created_at": datetime.now().isoformat(),
					}

					orders.append(order)

				except CSVParseError as e:
					errors.append(str(e))
				except Exception as e:
					errors.append(f"Row {row_num}: Unexpected error - {e!s}")

		except Exception as e:
			errors.append(f"CSV parsing error: {e!s}")

		return orders, errors


class CryptoExchangeCSVParser:
	"""Parser for crypto exchange purchase history CSV.

	Expected headers:
	Date(UTC+1);Method;Spend Amount;Receive Amount;Fee;Price;Status;Transaction ID

	Mappings:
	- Date: timestamp -> YYYY-MM-DD
	- Spend Amount: e.g. '50.00 EUR' -> amount_eur (gross before fee) minus Fee? We'll store net = spend amount
	- Receive Amount: '0.00279397 BTC' -> shares + symbol
	- Fee: '1.00 EUR' (ignored for now; could subtract from amount)
	- Price: '17537.76883789 BTC/EUR' -> price_per_share, currency
	- Status: Successful -> Finalizada else Rechazada
	- Transaction ID -> notes

	All rows assumed BUY orders.
	"""

	def parse_csv(self, csv_content: str) -> tuple[list[dict[str, Any]], list[str]]:
		"""Parse crypto exchange CSV content."""
		orders: list[dict[str, Any]] = []
		errors: list[str] = []
		RAW_MIN_COLUMNS = 8

		# Remove BOM if present (common in Windows UTF-8 files)
		csv_content = csv_content.lstrip("\ufeff")

		lines = [line for line in csv_content.splitlines() if line.strip()]
		logger.debug(f"CryptoExchangeCSVParser: Processing {len(lines)} lines")
		if not lines:
			return orders, ["Empty CSV content"]

		delimiter = ";" if ";" in lines[0] else ","
		header = lines[0].split(delimiter)
		if len(header) < RAW_MIN_COLUMNS:
			errors.append("Missing headers for crypto CSV")
			return orders, errors

		for row_num, line in enumerate(lines):
			if row_num == 0:  # Skip header
				continue
			parts = line.split(delimiter)
			if len(parts) < RAW_MIN_COLUMNS:
				errors.append(f"Row {row_num}: Incomplete row")
				continue

			result = self._parse_row(parts, row_num)
			if isinstance(result, str):
				errors.append(result)
			elif result:
				orders.append(result)

		return orders, errors

	def _parse_row(self, parts: list[str], row_num: int) -> dict[str, Any] | str | None:
		"""Process a single row from the crypto CSV."""
		raw_min_columns = 8
		# Extract first columns manually to avoid slice indexing issues with some linters
		if len(parts) < raw_min_columns:
			return f"Row {row_num}: Incomplete row"

		# Take only the columns we need
		date_raw = parts[0].strip()
		_method = parts[1].strip()
		spend_raw = parts[2].strip()
		receive_raw = parts[3].strip()
		fee_raw = parts[4].strip()
		price_raw = parts[5].strip()
		status_raw = parts[6].strip()
		tx_id = parts[7].strip()

		if not date_raw and not spend_raw:
			return None

		try:
			from datetime import datetime as _dt

			date_part = date_raw.split()[0]
			parsed_dt = _dt.strptime(date_part, "%d/%m/%Y") if "/" in date_part else _dt.strptime(date_part, "%Y-%m-%d")
			date_iso = parsed_dt.strftime("%Y-%m-%d")
		except Exception:
			return f"Row {row_num}: Invalid date '{date_raw}'"

		try:
			amt_value, _amt_curr = spend_raw.split()
			amount_eur = float(amt_value)
		except Exception:
			return f"Row {row_num}: Invalid spend amount '{spend_raw}'"

		try:
			fee_value = float(fee_raw.split()[0]) if fee_raw else 0.0
		except Exception:
			fee_value = 0.0

		try:
			recv_value, recv_symbol = receive_raw.split()
			shares = float(recv_value)
		except Exception:
			return f"Row {row_num}: Invalid receive amount '{receive_raw}'"

		try:
			price_val, pair = price_raw.split()
			price_per_share = float(price_val)
			_base_sym, fiat = pair.split("/")
		except Exception:
			return f"Row {row_num}: Invalid price '{price_raw}'"

		status = "Finalizada" if status_raw.lower().startswith("success") else "Rechazada"
		return {
			"id": str(uuid.uuid4()),
			"date": date_iso,
			"isin": recv_symbol.upper(),
			"amount_eur": amount_eur,
			"shares": shares,
			"order_type": "buy",
			"status": status,
			"price_per_share": price_per_share,
			"price_currency": fiat.upper(),
			"price_date": date_iso,
			"asset_type": "Crypto",
			"notes": f"Fee {fee_value} EUR | Tx {tx_id}",
			"created_at": _dt.now().isoformat(),
		}


def parse_spanish_csv(csv_content: str, encoding: str = "utf-8") -> tuple[list[dict[str, Any]], list[str]]:
	"""
	Convenience function to parse Spanish bank CSV format.

	Args:
		csv_content: CSV file content as string
		encoding: File encoding (default: utf-8)

	Returns:
		Tuple of (parsed_orders, errors)
	"""
	parser = SpanishOrderCSVParser(encoding=encoding)
	return parser.parse_csv(csv_content)
