"""Manual calculation for IE0032126645 to verify cost basis."""

from decimal import Decimal

orders = [
    ("2022-09-29", "buy", Decimal("4.63"), Decimal("200.00")),
    ("2022-11-03", "buy", Decimal("3.33"), Decimal("150.00")),
    ("2022-12-12", "buy", Decimal("3.36"), Decimal("150.00")),
    ("2023-01-05", "buy", Decimal("5.84"), Decimal("250.00")),
    ("2023-02-02", "buy", Decimal("5.54"), Decimal("249.90")),
    ("2023-03-01", "buy", Decimal("5.70"), Decimal("250.00")),
    ("2023-03-31", "buy", Decimal("2.22"), Decimal("100.00")),
    ("2023-08-30", "buy", Decimal("1.01"), Decimal("50.00")),
    ("2023-11-17", "buy", Decimal("7.05"), Decimal("350.00")),
    ("2023-12-25", "buy", Decimal("4.85"), Decimal("250.00")),
    ("2025-01-26", "sell", Decimal("14.30"), Decimal("1000.34")),  # SELL
    ("2025-07-10", "buy", Decimal("3.85"), Decimal("250.00")),
    ("2025-07-30", "buy", Decimal("5.21"), Decimal("350.00")),
    ("2025-10-02", "buy", Decimal("4.32"), Decimal("300.00")),
]

total_shares = Decimal("0")
total_cost = Decimal("0")
average_cost = Decimal("0")

print("CORRECTED CALCULATION (with fix):")
print("=" * 80)

for date, order_type, shares, amount in orders:
    if order_type == "sell":
        # For sells: reduce by (shares * average_cost)
        cost_reduction = shares * average_cost
        total_shares -= shares
        total_cost -= cost_reduction
        print(f"{date} SELL {shares:7.2f} shares @ €{amount/shares:6.2f}/share (proceeds: €{amount:8.2f})")
        print(f"         Cost reduction: {shares:7.2f} × €{average_cost:6.2f} = €{cost_reduction:8.2f}")
        print(f"         → Shares: {total_shares:7.2f}, Cost: €{total_cost:9.2f}, Avg: €{average_cost:6.2f}")
    else:  # buy
        total_shares += shares
        total_cost += amount
        average_cost = total_cost / total_shares if total_shares > 0 else Decimal("0")
        price_per_share = amount / shares
        print(f"{date} BUY  {shares:7.2f} shares @ €{price_per_share:6.2f}/share (cost: €{amount:8.2f})")
        print(f"         → Shares: {total_shares:7.2f}, Cost: €{total_cost:9.2f}, Avg: €{average_cost:6.2f}")

print("\n" + "=" * 80)
print(f"FINAL POSITION:")
print(f"  Total Shares: {total_shares:7.2f}")
print(f"  Total Cost (basis): €{total_cost:9.2f}")
print(f"  Average Cost/Share: €{average_cost:9.2f}")
print()

# Calculate with current price
current_price = Decimal("70.40")  # From the screenshot
current_value = total_shares * current_price
unrealized_pnl = current_value - total_cost
unrealized_pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else Decimal("0")

print(f"CURRENT VALUATION @ €{current_price}/share:")
print(f"  Current Value: €{current_value:9.2f}")
print(f"  Unrealized P&L: €{unrealized_pnl:9.2f} ({unrealized_pnl_pct:+.2f}%)")
print()

# Compare with bank's numbers
print("BANK'S NUMBERS:")
print(f"  Invested: €2,240.27")
print(f"  Current: €3,020.26")
print(f"  Gain: €779.99 (34.82%)")
print()

# Calculate what we're showing now (with OLD WRONG code)
print("=" * 80)
print("OLD CALCULATION (current backend - WRONG):")
total_shares_old = Decimal("0")
total_cost_old = Decimal("0")

for date, order_type, shares, amount in orders:
    if order_type == "sell":
        # OLD WRONG WAY: subtract sell proceeds
        total_shares_old -= shares
        total_cost_old -= amount  # WRONG!
    else:
        total_shares_old += shares
        total_cost_old += amount

avg_cost_old = total_cost_old / total_shares_old if total_shares_old > 0 else Decimal("0")
current_value_old = total_shares_old * current_price

print(f"  Total Shares: {total_shares_old:7.2f}")
print(f"  Total Cost (WRONG): €{total_cost_old:9.2f}")
print(f"  Average Cost: €{avg_cost_old:9.2f}")
print(f"  Current Value: €{current_value_old:9.2f}")
print(f"  P&L (WRONG): €{current_value_old - total_cost_old:9.2f}")
