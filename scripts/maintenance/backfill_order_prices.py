"""Backfill historical prices for existing orders."""

import asyncio
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH))

from app.config import settings  # noqa: E402
from app.services.storage_service import StorageService  # noqa: E402
from app.services.yahoo_finance import YahooFinanceService  # noqa: E402

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def backfill_prices():
	"""Backfill price_per_share for all existing orders."""
	users_file = settings.DATA_DIR / "users.json"

	if not users_file.exists():
		logger.error(f"Users file not found: {users_file}")
		return

	logger.info("Loading users data...")
	users = StorageService.load_json(users_file, default={})

	total_orders = 0
	updated_orders = 0
	skipped_orders = 0

	for username, user_data in users.items():
		logger.info(f"\nProcessing user: {username}")
		orders = user_data.get("orders", [])

		if not orders:
			logger.info(f"  No orders found for {username}")
			continue

		logger.info(f"  Found {len(orders)} orders")

		# Backfill prices
		updated = await YahooFinanceService.backfill_order_prices(orders)

		# Count stats
		for order in updated:
			total_orders += 1
			if "price_per_share" in order and order["price_per_share"] is not None:
				if order.get("price_date") == order.get("date"):
					updated_orders += 1
				else:
					skipped_orders += 1

		# Update user data
		user_data["orders"] = updated

	# Save updated data
	logger.info("\nSaving updated data...")
	StorageService.save_json(users_file, users)

	logger.info("\n=== Backfill Summary ===")
	logger.info(f"Total orders processed: {total_orders}")
	logger.info(f"Orders with prices added: {updated_orders}")
	logger.info(f"Orders already had prices: {skipped_orders}")
	success_rate = updated_orders / total_orders * 100 if total_orders else 0
	logger.info(f"Success rate: {success_rate:.1f}%")


if __name__ == "__main__":
	asyncio.run(backfill_prices())
