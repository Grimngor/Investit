"""
Migration script: Holdings → Orders data model

This script migrates the legacy holdings-based data model to the new 
order-based model as specified in PRD v2.

Migration strategy:
1. Backup existing users.json
2. For each user with holdings:
   - Convert each holding to a single "buy" order
   - Preserve all available data (date, amount, shares)
   - Generate unique order IDs
3. Create separate instruments.json with unique ISINs
4. Create empty prices.json and settings.json structures
5. Save migrated data

Usage:
    python migrate_holdings_to_orders.py [--dry-run] [--backup-dir PATH]
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import shutil
import sys

# Add backend to path for imports
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.storage_service import StorageService
from app.models.order import Order, Instrument


class HoldingsToOrdersMigration:
    """Handles migration from holdings-based to orders-based data model."""

    def __init__(self, data_dir: Path, backup_dir: Path):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.storage = StorageService()
        self.users_file = data_dir / "users.json"
        self.instruments_file = data_dir / "instruments.json"
        self.prices_file = data_dir / "prices.json"
        self.settings_file = data_dir / "settings.json"

    def create_backup(self) -> Path:
        """Create timestamped backup of users.json."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"users_backup_{timestamp}.json"
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.users_file, backup_file)
        
        print(f"✅ Backup created: {backup_file}")
        return backup_file

    def convert_holding_to_order(self, holding: Dict[str, Any], username: str, index: int) -> Dict[str, Any]:
        """Convert a single holding to an order."""
        # Generate order ID
        order_id = f"{username}_{holding.get('symbol', 'unknown')}_{index}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate amount (quantity * purchase_price)
        quantity = holding.get("quantity", 0)
        purchase_price = holding.get("purchase_price", 0)
        amount_eur = quantity * purchase_price
        
        # Extract date
        purchase_date = holding.get("purchase_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Try to get ISIN from symbol (placeholder - will need ISIN lookup)
        symbol = holding.get("symbol", "UNKNOWN")
        isin = holding.get("isin", f"XX{symbol:0<10}")  # Placeholder ISIN
        
        order = {
            "id": order_id,
            "date": purchase_date,
            "isin": isin,
            "ticker": symbol,
            "amount_eur": amount_eur,
            "shares": quantity,
            "order_type": "buy",
            "status": "Finalizada",
            "notes": holding.get("notes", "Migrated from holdings"),
            "created_at": datetime.now().isoformat()
        }
        
        return order

    def extract_instrument(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Extract instrument data from a holding."""
        symbol = holding.get("symbol", "UNKNOWN")
        isin = holding.get("isin", f"XX{symbol:0<10}")
        
        instrument = {
            "isin": isin,
            "ticker": symbol,
            "name": holding.get("name", symbol),
            "instrument_type": holding.get("type", "Unknown"),
            "currency": holding.get("currency", "EUR"),
            "sector": holding.get("sector"),
            "region": holding.get("region"),
            "geography": holding.get("region"),
            "risk_rating": holding.get("risk_rating")
        }
        
        return instrument

    def migrate_user_holdings(self, username: str, user_data: Dict[str, Any]) -> tuple[List[Dict], List[Dict]]:
        """
        Migrate all holdings for a single user to orders.
        
        Returns:
            Tuple of (orders, instruments)
        """
        holdings = user_data.get("holdings", [])
        
        if not holdings:
            return [], []
        
        orders = []
        instruments = []
        
        for idx, holding in enumerate(holdings):
            # Convert to order
            order = self.convert_holding_to_order(holding, username, idx)
            orders.append(order)
            
            # Extract instrument
            instrument = self.extract_instrument(holding)
            instruments.append(instrument)
        
        return orders, instruments

    def run_migration(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute the full migration.
        
        Args:
            dry_run: If True, only report what would be done without saving
            
        Returns:
            Migration statistics
        """
        stats = {
            "users_processed": 0,
            "orders_created": 0,
            "instruments_created": 0,
            "users_with_holdings": 0,
            "errors": []
        }
        
        # Load existing users
        print(f"📂 Loading users from {self.users_file}")
        users = self.storage.load_json(self.users_file, default={})
        
        if not users:
            print("❌ No users found or file doesn't exist")
            return stats
        
        # Create backup
        if not dry_run:
            self.create_backup()
        
        # Collect all orders and instruments
        all_instruments = {}  # Use dict to deduplicate by ISIN
        
        for username, user_data in users.items():
            stats["users_processed"] += 1
            
            # Migrate holdings to orders
            orders, instruments = self.migrate_user_holdings(username, user_data)
            
            if orders:
                stats["users_with_holdings"] += 1
                stats["orders_created"] += len(orders)
                
                # Add orders to user
                user_data["orders"] = orders
                
                # Remove old holdings field
                if "holdings" in user_data:
                    del user_data["holdings"]
                
                # Collect unique instruments
                for instrument in instruments:
                    all_instruments[instrument["isin"]] = instrument
                
                print(f"  ✅ {username}: {len(orders)} orders created")
        
        stats["instruments_created"] = len(all_instruments)
        
        # Save migrated data
        if not dry_run:
            print("\n💾 Saving migrated data...")
            
            # Save updated users.json
            self.storage.save_json(self.users_file, users)
            print(f"  ✅ Saved {self.users_file}")
            
            # Save instruments.json
            instruments_list = list(all_instruments.values())
            self.storage.save_json(self.instruments_file, instruments_list)
            print(f"  ✅ Saved {self.instruments_file} ({len(instruments_list)} instruments)")
            
            # Create empty prices.json
            self.storage.save_json(self.prices_file, {})
            print(f"  ✅ Created {self.prices_file}")
            
            # Create empty settings.json
            self.storage.save_json(self.settings_file, {})
            print(f"  ✅ Created {self.settings_file}")
        else:
            print("\n🔍 DRY RUN - No files modified")
        
        return stats


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate holdings-based data to orders-based model"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("data/backups"),
        help="Directory for backups (default: data/backups)"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory containing users.json (default: data)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Holdings → Orders Migration")
    print("=" * 60)
    print()
    
    # Initialize migration
    migration = HoldingsToOrdersMigration(
        data_dir=args.data_dir,
        backup_dir=args.backup_dir
    )
    
    # Run migration
    stats = migration.run_migration(dry_run=args.dry_run)
    
    # Print summary
    print("\n" + "=" * 60)
    print("  Migration Summary")
    print("=" * 60)
    print(f"  Users processed: {stats['users_processed']}")
    print(f"  Users with holdings: {stats['users_with_holdings']}")
    print(f"  Orders created: {stats['orders_created']}")
    print(f"  Instruments created: {stats['instruments_created']}")
    
    if stats["errors"]:
        print(f"\n  ⚠️  Errors ({len(stats['errors'])}):")
        for error in stats["errors"]:
            print(f"    - {error}")
    else:
        print("\n  ✅ Migration completed successfully!")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
