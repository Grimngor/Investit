"""
Backup and export service for data files.

Implements PRD Section 10 requirement:
- Daily rotated backups with 7-day retention
- Export portfolio data for download
"""

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.services.storage_service import StorageService


class BackupService:
    """Handles backup and export operations for user data."""

    def __init__(self, data_dir: Path = Path("data"), backup_dir: Path = Path("data/backups")):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.storage = StorageService()
        self.retention_days = 7

    def create_backup(self, filename: str) -> Path:
        """
        Create a timestamped backup of a data file.

        Args:
            filename: Name of the file to backup (e.g., "users.json")

        Returns:
            Path to the created backup file
        """
        source_file = self.data_dir / filename
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped backup filename
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_file.stem}_backup_{timestamp}{source_file.suffix}"
        backup_file = self.backup_dir / backup_name

        # Copy file
        shutil.copy2(source_file, backup_file)

        return backup_file

    def rotate_backups(self, filename_pattern: str = "*_backup_*") -> int:
        """
        Delete backups older than retention_days.

        Args:
            filename_pattern: Glob pattern to match backup files

        Returns:
            Number of backups deleted
        """
        if not self.backup_dir.exists():
            return 0

        cutoff_date = datetime.now(UTC) - timedelta(days=self.retention_days)
        deleted_count = 0

        for backup_file in self.backup_dir.glob(filename_pattern):
            if backup_file.is_file():
                # Get file modification time
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime, tz=UTC)

                if mtime < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1

        return deleted_count

    def daily_backup(self) -> dict[str, Any]:
        """
        Perform daily backup of all data files with rotation.

        Returns:
            Dict with backup statistics
        """
        stats = {"backups_created": [], "backups_deleted": 0, "errors": []}

        # Files to backup
        files_to_backup = [
            "users.json",
            "instruments.json",
            "prices.json",
            "settings.json",
        ]

        for filename in files_to_backup:
            try:
                source = self.data_dir / filename
                if source.exists():
                    backup_path = self.create_backup(filename)
                    stats["backups_created"].append(str(backup_path))
            except Exception as e:
                stats["errors"].append(f"{filename}: {e!s}")

        # Rotate old backups
        try:
            stats["backups_deleted"] = self.rotate_backups()
        except Exception as e:
            stats["errors"].append(f"Rotation error: {e!s}")

        return stats

    def export_user_portfolio(self, username: str) -> dict[str, Any]:
        """
        Export a user's complete portfolio data for download.

        Args:
            username: Username to export

        Returns:
            Dict containing user's orders, instruments, and summary
        """
        # Load users
        users_file = self.data_dir / "users.json"
        users = self.storage.load_json(users_file, default={})

        if username not in users:
            raise ValueError(f"User not found: {username}")

        user_data = users[username]

        # Load instruments and prices
        instruments_file = self.data_dir / "instruments.json"
        prices_file = self.data_dir / "prices.json"

        instruments = self.storage.load_json(instruments_file, default=[])
        prices = self.storage.load_json(prices_file, default={})

        # Get user's orders
        orders = user_data.get("orders", [])

        # Filter instruments and prices for user's ISINs
        user_isins = {order.get("isin") for order in orders if order.get("isin")}

        user_instruments = [inst for inst in instruments if inst.get("isin") in user_isins]

        user_prices = {isin: price for isin, price in prices.items() if isin in user_isins}

        # Build export
        export_data = {
            "export_date": datetime.now(UTC).isoformat(),
            "username": username,
            "orders": orders,
            "instruments": user_instruments,
            "prices": user_prices,
            "summary": {
                "total_orders": len(orders),
                "unique_instruments": len(user_instruments),
            },
        }

        return export_data

    def export_user_to_json(self, username: str, output_path: Path) -> Path:
        """
        Export user portfolio to a JSON file.

        Args:
            username: Username to export
            output_path: Where to save the export

        Returns:
            Path to the exported file
        """
        export_data = self.export_user_portfolio(username)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage.save_json(output_path, export_data)

        return output_path

    def list_backups(self, filename_pattern: str = "*_backup_*") -> list[dict[str, Any]]:
        """
        List all available backups.

        Args:
            filename_pattern: Glob pattern to match backup files

        Returns:
            List of backup file info (name, size, date)
        """
        if not self.backup_dir.exists():
            return []

        backups = []

        for backup_file in sorted(self.backup_dir.glob(filename_pattern), reverse=True):
            if backup_file.is_file():
                stat = backup_file.stat()
                backups.append(
                    {
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                    }
                )

        return backups
