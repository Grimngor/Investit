"""Tests for storage service with atomic writes and file locking."""

import json
import pytest
import tempfile
from pathlib import Path
from app.services.storage_service import StorageService


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
        f.write(json.dumps({"test": "data"}))
    yield temp_path
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_json_existing_file(temp_json_file):
    """Test loading JSON from existing file."""
    data = StorageService.load_json(temp_json_file)
    assert data == {"test": "data"}


def test_load_json_nonexistent_file(temp_dir):
    """Test loading JSON from nonexistent file returns default."""
    nonexistent = temp_dir / "nonexistent.json"
    data = StorageService.load_json(nonexistent, default={"default": "value"})
    assert data == {"default": "value"}


def test_load_json_empty_file(temp_dir):
    """Test loading JSON from empty file returns default."""
    empty_file = temp_dir / "empty.json"
    empty_file.write_text("", encoding="utf-8")
    data = StorageService.load_json(empty_file, default={})
    assert data == {}


def test_load_json_invalid_json(temp_dir):
    """Test loading invalid JSON returns default."""
    invalid_file = temp_dir / "invalid.json"
    invalid_file.write_text("not valid json {", encoding="utf-8")
    data = StorageService.load_json(invalid_file, default={"error": "handled"})
    assert data == {"error": "handled"}


def test_save_json_new_file(temp_dir):
    """Test saving JSON to new file."""
    new_file = temp_dir / "new.json"
    test_data = {"key": "value", "number": 42}

    StorageService.save_json(new_file, test_data)

    assert new_file.exists()
    loaded = json.loads(new_file.read_text(encoding="utf-8"))
    assert loaded == test_data


def test_save_json_overwrite_existing(temp_json_file):
    """Test saving JSON overwrites existing file atomically."""
    new_data = {"updated": "data", "count": 123}

    StorageService.save_json(temp_json_file, new_data)

    loaded = json.loads(temp_json_file.read_text(encoding="utf-8"))
    assert loaded == new_data


def test_save_json_creates_directory(temp_dir):
    """Test saving JSON creates parent directories."""
    nested_file = temp_dir / "nested" / "dir" / "file.json"
    test_data = {"nested": True}

    StorageService.save_json(nested_file, test_data)

    assert nested_file.exists()
    loaded = json.loads(nested_file.read_text(encoding="utf-8"))
    assert loaded == test_data


def test_update_json_new_file(temp_dir):
    """Test update_json creates new file with default."""
    new_file = temp_dir / "update_new.json"

    def add_field(data):
        data["added"] = "field"
        return data

    result = StorageService.update_json(new_file, add_field, default={"initial": "data"})

    assert result == {"initial": "data", "added": "field"}
    loaded = json.loads(new_file.read_text(encoding="utf-8"))
    assert loaded == result


def test_update_json_existing_file(temp_json_file):
    """Test update_json modifies existing file atomically."""

    def increment_counter(data):
        data["counter"] = data.get("counter", 0) + 1
        return data

    result = StorageService.update_json(temp_json_file, increment_counter)

    assert result["counter"] == 1
    loaded = json.loads(temp_json_file.read_text(encoding="utf-8"))
    assert loaded["counter"] == 1


def test_update_json_multiple_updates(temp_json_file):
    """Test multiple sequential updates."""

    def add_item(data):
        items = data.get("items", [])
        items.append(len(items) + 1)
        data["items"] = items
        return data

    for i in range(3):
        StorageService.update_json(temp_json_file, add_item)

    loaded = json.loads(temp_json_file.read_text(encoding="utf-8"))
    assert loaded["items"] == [1, 2, 3]


def test_atomic_write_no_corruption_on_crash(temp_dir):
    """Test atomic write doesn't corrupt file if error occurs during write."""
    target_file = temp_dir / "atomic.json"
    target_file.write_text('{"original": "data"}', encoding="utf-8")

    # Simulate write failure
    class WriteError(Exception):
        pass

    original_replace = Path.replace

    def failing_replace(self, target):
        raise WriteError("Simulated failure")

    Path.replace = failing_replace

    try:
        StorageService.save_json(target_file, {"should": "fail"})
    except WriteError:
        pass
    finally:
        Path.replace = original_replace

    # Original file should still be intact
    loaded = json.loads(target_file.read_text(encoding="utf-8"))
    assert loaded == {"original": "data"}
