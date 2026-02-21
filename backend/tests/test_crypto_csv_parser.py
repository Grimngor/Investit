"""Tests for CryptoExchangeCSVParser parsing exchange history CSV."""

from app.utils.csv_parser import CryptoExchangeCSVParser

SAMPLE_CSV = (
	"Date(UTC+1);Method;Spend Amount;Receive Amount;Fee;Price;Status;Transaction ID\n"
	"2022-11-09 14:08:50;Credit Card;50.00 EUR;0.00279397 BTC;1.00 EUR;"
	"17537.76883789 BTC/EUR;Successful;N01286829915502821376110922\n"
)


def test_crypto_csv_parser_basic():
	parser = CryptoExchangeCSVParser()
	orders, errors = parser.parse_csv(SAMPLE_CSV)
	assert not errors
	assert len(orders) == 1
	order = orders[0]
	assert order["isin"] == "BTC"
	assert order["asset_type"] == "Crypto"
	assert order["shares"] == 0.00279397
	assert order["amount_eur"] == 50.00
	assert order["price_per_share"] > 10000
	assert order["status"] == "Finalizada"
