"""Tests for backup service."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.services.backup_service import BackupService


@pytest.fixture
def temp_data_dir(tmp_path):
	"""Create temporary data directory with test files."""
	data_dir = tmp_path / "data"
	data_dir.mkdir(exist_ok=True)

	# Create test users.json
	users = {
		"testuser": {
			"username": "testuser",
			"hashed_password": "hash123",
			"is_active": True,
			"orders": [
				{
					"id": "order1",
					"date": "2024-01-01",
					"isin": "US0378331005",
					"shares": 10,
					"amount_eur": 1500.0,
					"order_type": "buy",
					"status": "Finalizada",
				}
			],
		}
	}

	(data_dir / "users.json").write_text(json.dumps(users, indent=2))
	(data_dir / "instruments.json").write_text(json.dumps([], indent=2))
	(data_dir / "prices.json").write_text(json.dumps({}, indent=2))
	(data_dir / "settings.json").write_text(json.dumps({}, indent=2))

	return data_dir


@pytest.fixture
def backup_service(temp_data_dir, tmp_path):
	"""Create BackupService instance with temp directories."""
	backup_dir = tmp_path / "backups"
	return BackupService(data_dir=temp_data_dir, backup_dir=backup_dir)


def test_create_backup(backup_service, temp_data_dir):
	"""Test creating a single backup file."""
	backup_path = backup_service.create_backup("users.json")

	assert backup_path.exists()
	assert "users_backup_" in backup_path.name
	assert backup_path.suffix == ".json"

	# Verify content matches original
	original = (temp_data_dir / "users.json").read_text()
	backup = backup_path.read_text()
	assert original == backup


def test_create_backup_nonexistent_file(backup_service):
	"""Test backing up a file that doesn't exist."""
	with pytest.raises(FileNotFoundError):
		backup_service.create_backup("nonexistent.json")


def test_rotate_backups(backup_service, tmp_path):
	"""Test backup rotation deletes old files."""
	backup_dir = tmp_path / "backups"
	backup_dir.mkdir(parents=True, exist_ok=True)

	# Create old backup (8 days ago)
	old_backup = backup_dir / "users_backup_20241015_120000.json"
	old_backup.write_text("{}")
	old_time = datetime.now() - timedelta(days=8)
	old_backup.touch()
	# Set modification time to 8 days ago
	import os
	import time

	os.utime(old_backup, (time.time(), old_time.timestamp()))

	# Create recent backup (1 day ago)
	recent_backup = backup_dir / "users_backup_20241022_120000.json"
	recent_backup.write_text("{}")

	# Rotate
	deleted = backup_service.rotate_backups()

	assert deleted == 1
	assert not old_backup.exists()
	assert recent_backup.exists()


def test_daily_backup(backup_service, temp_data_dir):
	"""Test daily backup creates all files."""
	stats = backup_service.daily_backup()

	assert len(stats["backups_created"]) == 4  # users, instruments, prices, settings
	assert stats["backups_deleted"] == 0
	assert len(stats["errors"]) == 0

	# Verify all backups exist
	for backup_path in stats["backups_created"]:
		assert Path(backup_path).exists()


def test_export_user_portfolio(backup_service, temp_data_dir):
	"""Test exporting a user's portfolio."""
	export = backup_service.export_user_portfolio("testuser")

	assert export["username"] == "testuser"
	assert len(export["orders"]) == 1
	assert export["orders"][0]["isin"] == "US0378331005"
	assert export["summary"]["total_orders"] == 1
	assert "export_date" in export


def test_export_user_not_found(backup_service):
	"""Test exporting non-existent user."""
	with pytest.raises(ValueError, match="User not found"):
		backup_service.export_user_portfolio("nonexistent")


def test_export_user_to_json(backup_service, tmp_path):
	"""Test exporting user to JSON file."""
	output_path = tmp_path / "exports" / "testuser_export.json"

	result_path = backup_service.export_user_to_json("testuser", output_path)

	assert result_path == output_path
	assert output_path.exists()

	# Verify content
	data = json.loads(output_path.read_text())
	assert data["username"] == "testuser"
	assert len(data["orders"]) == 1


def test_list_backups(backup_service, tmp_path):
	"""Test listing all backups."""
	backup_dir = tmp_path / "backups"
	backup_dir.mkdir(parents=True, exist_ok=True)

	# Create some backups
	(backup_dir / "users_backup_20241023_100000.json").write_text("{}")
	(backup_dir / "users_backup_20241023_110000.json").write_text("{}")

	backups = backup_service.list_backups()

	assert len(backups) == 2
	assert all("filename" in b for b in backups)
	assert all("size_bytes" in b for b in backups)
	assert all("modified" in b for b in backups)


def test_list_backups_empty(backup_service):
	"""Test listing backups when none exist."""
	backups = backup_service.list_backups()
	assert backups == []
