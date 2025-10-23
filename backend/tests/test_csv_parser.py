"""Tests for CSV parser utility."""

import pytest
from app.utils.csv_parser import SpanishOrderCSVParser, parse_spanish_csv, CSVParseError


def test_parse_valid_csv():
    """Test parsing a valid Spanish CSV."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE0032126645,500.00 EUR,12.345,Finalizada
20/02/2024,IE00BYX5NX33,1000.50,25.678,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 2
    assert len(errors) == 0

    # Check first order
    assert orders[0]["date"] == "2024-01-15"
    assert orders[0]["isin"] == "IE0032126645"
    assert orders[0]["amount_eur"] == 500.00
    assert orders[0]["shares"] == 12.345
    assert orders[0]["order_type"] == "buy"
    assert orders[0]["status"] == "Finalizada"


def test_parse_csv_with_rejected_orders():
    """Test that rejected orders are skipped."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE0032126645,500.00,12.345,Finalizada
20/02/2024,IE00BYX5NX33,1000.50,25.678,Rechazada
25/03/2024,IE0031786696,750.00,18.123,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 2  # Rejected order should be skipped
    assert len(errors) == 0
    assert orders[0]["isin"] == "IE0032126645"
    assert orders[1]["isin"] == "IE0031786696"


def test_parse_csv_with_sell_order():
    """Test parsing CSV with negative amount (sell order)."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE0032126645,-500.00,12.345,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 1
    assert orders[0]["order_type"] == "sell"
    assert orders[0]["amount_eur"] == 500.00  # Should be positive


def test_parse_csv_with_spanish_decimal_format():
    """Test parsing amounts with Spanish format (comma as decimal)."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE0032126645,"1.234,56 EUR",12.345,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 1
    assert orders[0]["amount_eur"] == 1234.56


def test_parse_csv_with_encoding_issue():
    """Test parsing CSV with encoding issue in header (Nº vs NÂº)."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,NÂº de participaciones,Estado
15/01/2024,IE0032126645,500.00,12.345,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 1
    assert len(errors) == 0


def test_parse_csv_with_invalid_date():
    """Test parsing CSV with invalid date format."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
2024-01-15,IE0032126645,500.00,12.345,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 0
    assert len(errors) == 1
    assert "Invalid date format" in errors[0]


def test_parse_csv_with_invalid_isin():
    """Test parsing CSV with invalid ISIN."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,INVALID,500.00,12.345,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 0
    assert len(errors) == 1
    assert "Invalid ISIN length" in errors[0]


def test_parse_csv_with_missing_field():
    """Test parsing CSV with missing required field."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,,500.00,12.345,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 0
    assert len(errors) == 1
    assert "Missing ISIN" in errors[0]


def test_parse_csv_with_missing_header():
    """Test parsing CSV with missing required header."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Estado
15/01/2024,IE0032126645,500.00,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 0
    assert len(errors) == 1
    assert "Missing required headers" in errors[0]


def test_parse_empty_csv():
    """Test parsing empty CSV."""
    csv_content = ""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 0
    # Empty CSV may or may not produce errors depending on implementation


def test_parser_shares_format():
    """Test parsing shares with comma decimal separator."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
15/01/2024,IE0032126645,500.00,"12,345",Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 1
    assert orders[0]["shares"] == 12.345


def test_parser_multiple_errors():
    """Test that parser collects multiple errors."""
    csv_content = """Fecha de la orden,ISIN,Importe estimado,Nº de participaciones,Estado
INVALID,IE0032126645,500.00,12.345,Finalizada
15/01/2024,BADLENGTH,500.00,12.345,Finalizada
20/02/2024,IE00BYX5NX33,,12.345,Finalizada"""

    orders, errors = parse_spanish_csv(csv_content)

    assert len(orders) == 0
    assert len(errors) >= 3  # Should have multiple errors
