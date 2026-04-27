"""Migrate legacy holdings data into the order-based data model."""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.services.storage_service import StorageService  # noqa: E402


class HoldingsToOrdersMigration:
	"""Handle migration from holdings-based data to orders-based data."""

	def __init__(self, data_dir: Path, backup_dir: Path) -> None:
		self.data_dir = data_dir
		self.backup_dir = backup_dir
		self.storage = StorageService()
		self.users_file = data_dir / "users.json"
		self.instruments_file = data_dir / "instruments.json"
		self.prices_file = data_dir / "prices.json"

	def create_backup(self) -> Path:
		"""Create a timestamped backup of users.json."""
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		backup_file = self.backup_dir / f"users_backup_{timestamp}.json"

		self.backup_dir.mkdir(parents=True, exist_ok=True)
		shutil.copy2(self.users_file, backup_file)

		print(f"[OK] Backup created: {backup_file}")
		return backup_file

	def convert_holding_to_order(self, holding: dict[str, Any], username: str, index: int) -> dict[str, Any]:
		"""Convert one legacy holding record to one buy order."""
		symbol = holding.get("symbol", "UNKNOWN")
		order_id = f"{username}_{symbol}_{index}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
		quantity = holding.get("quantity", 0)
		purchase_price = holding.get("purchase_price", 0)
		amount_eur = quantity * purchase_price
		purchase_date = holding.get("purchase_date", datetime.now().strftime("%Y-%m-%d"))
		isin = holding.get("isin", f"XX{symbol:0<10}")

		return {
			"id": order_id,
			"date": purchase_date,
			"isin": isin,
			"ticker": symbol,
			"amount_eur": amount_eur,
			"shares": quantity,
			"order_type": "buy",
			"status": "Finalizada",
			"notes": holding.get("notes", "Migrated from holdings"),
			"created_at": datetime.now().isoformat(),
		}

	def extract_instrument(self, holding: dict[str, Any]) -> dict[str, Any]:
		"""Extract one instrument record from a legacy holding."""
		symbol = holding.get("symbol", "UNKNOWN")
		isin = holding.get("isin", f"XX{symbol:0<10}")

		return {
			"isin": isin,
			"ticker": symbol,
			"name": holding.get("name", symbol),
			"instrument_type": holding.get("type", "Unknown"),
			"currency": holding.get("currency", "EUR"),
			"sector": holding.get("sector"),
			"region": holding.get("region"),
			"geography": holding.get("region"),
			"risk_rating": holding.get("risk_rating"),
		}

	def migrate_user_holdings(self, username: str, user_data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
		"""Migrate all legacy holdings for one user."""
		holdings = user_data.get("holdings", [])
		if not holdings:
			return [], []

		orders = []
		instruments = []
		for idx, holding in enumerate(holdings):
			orders.append(self.convert_holding_to_order(holding, username, idx))
			instruments.append(self.extract_instrument(holding))

		return orders, instruments

	def run_migration(self, dry_run: bool = False) -> dict[str, Any]:
		"""Execute the holdings-to-orders migration."""
		stats: dict[str, Any] = {
			"users_processed": 0,
			"orders_created": 0,
			"instruments_created": 0,
			"users_with_holdings": 0,
			"errors": [],
		}

		print(f"Loading users from {self.users_file}")
		users = self.storage.load_json(self.users_file, default={})
		if not users:
			print("[ERROR] No users found or users.json does not exist")
			return stats

		if not dry_run:
			self.create_backup()

		all_instruments: dict[str, dict[str, Any]] = {}
		for username, user_data in users.items():
			stats["users_processed"] += 1
			orders, instruments = self.migrate_user_holdings(username, user_data)

			if not orders:
				continue

			stats["users_with_holdings"] += 1
			stats["orders_created"] += len(orders)
			user_data["orders"] = orders
			user_data.pop("holdings", None)

			for instrument in instruments:
				all_instruments[instrument["isin"]] = instrument

			print(f"  [OK] {username}: {len(orders)} orders created")

		stats["instruments_created"] = len(all_instruments)

		if dry_run:
			print("\nDRY RUN - No files modified")
			return stats

		print("\nSaving migrated data...")
		self.storage.save_json(self.users_file, users)
		print(f"  [OK] Saved {self.users_file}")

		instruments_list = list(all_instruments.values())
		self.storage.save_json(self.instruments_file, instruments_list)
		print(f"  [OK] Saved {self.instruments_file} ({len(instruments_list)} instruments)")

		self.storage.save_json(self.prices_file, {})
		print(f"  [OK] Created {self.prices_file}")

		return stats


def main() -> None:
	"""Run the migration from the command line."""
	parser = argparse.ArgumentParser(description="Migrate holdings-based data to the orders-based model")
	parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
	parser.add_argument("--backup-dir", type=Path, default=Path("data/backups"), help="Directory for backups")
	parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Data directory containing users.json")

	args = parser.parse_args()
	migration = HoldingsToOrdersMigration(data_dir=args.data_dir, backup_dir=args.backup_dir)
	stats = migration.run_migration(dry_run=args.dry_run)

	print("\nMigration Summary")
	print("=" * 60)
	print(f"Users processed: {stats['users_processed']}")
	print(f"Users with holdings: {stats['users_with_holdings']}")
	print(f"Orders created: {stats['orders_created']}")
	print(f"Instruments created: {stats['instruments_created']}")

	if stats["errors"]:
		print(f"\nErrors ({len(stats['errors'])}):")
		for error in stats["errors"]:
			print(f"- {error}")
	else:
		print("\nMigration completed successfully")


if __name__ == "__main__":
	main()
