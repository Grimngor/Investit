"""Test script to directly test crypto CSV parsing."""

from backend.app.utils.csv_parser import CryptoExchangeCSVParser

# Read the CSV file
csv_path = r"C:\Users\Javi\Downloads\Historial de compra de criptomonedas.csv"
with open(csv_path, "r", encoding="utf-8") as f:
	content = f.read()

print("=== CSV Content (first 200 chars) ===")
print(content[:200])
print()

print("=== First Line ===")
first_line = content.splitlines()[0]
print(repr(first_line))
print()

print("=== Auto-detection Check ===")
is_crypto = "Date(UTC" in first_line and "Spend Amount" in first_line and "Receive Amount" in first_line
print(f"Contains 'Date(UTC': {'Date(UTC' in first_line}")
print(f"Contains 'Spend Amount': {'Spend Amount' in first_line}")
print(f"Contains 'Receive Amount': {'Receive Amount' in first_line}")
print(f"Should detect as crypto CSV: {is_crypto}")
print()

print("=== Parsing CSV ===")
parser = CryptoExchangeCSVParser()
orders, errors = parser.parse_csv(content)

print(f"Orders parsed: {len(orders)}")
print(f"Errors: {len(errors)}")
print()

if errors:
	print("=== Errors ===")
	for error in errors[:5]:
		print(f"  - {error}")
	print()

if orders:
	print("=== First Order ===")
	print(orders[0])
	print()
	print("=== All Symbols ===")
	symbols = [o.get("isin") for o in orders]
	print(symbols)
