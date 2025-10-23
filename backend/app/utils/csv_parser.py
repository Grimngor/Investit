"""CSV parser for Spanish bank format order imports."""

import csv
from datetime import datetime
from typing import List, Dict, Any, Tuple
from io import StringIO
import re
import uuid


class CSVParseError(Exception):
    """Custom exception for CSV parsing errors."""

    pass


class SpanishOrderCSVParser:
    """
    Parser for Spanish bank CSV format.

    Expected CSV format per PRD:
    - Headers: Fecha de la orden, ISIN, Importe estimado, Nº de participaciones, Estado
    - Date format: DD/MM/YYYY
    - Amount format: can use ',' or '.' as decimal separator, may include ' EUR' suffix
    - Estado: 'Finalizada' (accept), 'Rechazada' (skip)
    - Note: Header 'Nº' may appear as 'NÂº' due to encoding issues
    """

    EXPECTED_HEADERS = ["Fecha de la orden", "ISIN", "Importe estimado", "Nº de participaciones", "Estado"]

    HEADER_VARIATIONS = {
        "Nº de participaciones": ["Nº de participaciones", "NÂº de participaciones", "N° de participaciones"],
    }

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
        except ValueError:
            raise CSVParseError(f"Row {row_num}: Invalid date format '{date_str}'. Expected DD/MM/YYYY")

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

            if last_comma_pos > last_dot_pos:
                # Spanish format: 1.234,56 (dot is thousands, comma is decimal)
                amount_str = amount_str.replace(".", "").replace(",", ".")
            else:
                # US format: 1,234.56 (comma is thousands, dot is decimal)
                amount_str = amount_str.replace(",", "")
        elif has_comma:
            # Only comma - assume it's decimal separator (Spanish format)
            amount_str = amount_str.replace(",", ".")
        # If only dot or neither, keep as is

        try:
            return float(amount_str)
        except ValueError:
            raise CSVParseError(f"Row {row_num}: Invalid amount format '{amount_str}'")

    def _parse_shares(self, shares_str: str, row_num: int) -> float:
        """
        Parse number of shares.

        Args:
            shares_str: Shares string
            row_num: Row number for error reporting

        Returns:
            Shares as float

        Raises:
            CSVParseError: If shares format is invalid
        """
        shares_str = shares_str.strip()

        # Handle comma as decimal separator
        shares_str = shares_str.replace(",", ".")

        try:
            shares = float(shares_str)
            if shares <= 0:
                raise CSVParseError(f"Row {row_num}: Shares must be positive, got {shares}")
            return shares
        except ValueError:
            raise CSVParseError(f"Row {row_num}: Invalid shares format '{shares_str}'")

    def parse_csv(self, csv_content: str) -> Tuple[List[Dict[str, Any]], List[str]]:
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
            # Parse CSV
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)

            # Normalize headers
            if reader.fieldnames:
                reader.fieldnames = [self._normalize_header(h) for h in reader.fieldnames]

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
                    if len(isin) != 12:
                        errors.append(f"Row {row_num}: Invalid ISIN length '{isin}' (expected 12 characters)")
                        continue

                    # Parse amount
                    amount_str = row.get("Importe estimado", "").strip()
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
                        "created_at": datetime.now().isoformat()
                    }

                    orders.append(order)

                except CSVParseError as e:
                    errors.append(str(e))
                except Exception as e:
                    errors.append(f"Row {row_num}: Unexpected error - {str(e)}")

        except Exception as e:
            errors.append(f"CSV parsing error: {str(e)}")

        return orders, errors


def parse_spanish_csv(csv_content: str, encoding: str = "utf-8") -> Tuple[List[Dict[str, Any]], List[str]]:
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
