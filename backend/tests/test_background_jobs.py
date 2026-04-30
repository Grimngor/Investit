"""Tests for the lightweight background job registry."""

from app.services.background_jobs import BackgroundJobRegistry


def test_job_registry_prevents_duplicate_active_jobs() -> None:
	"""Queued and running jobs are treated as active until completed."""
	registry = BackgroundJobRegistry()

	first = registry.queue("alice", "price_fetch", count=2)
	second = registry.queue("alice", "price_fetch", count=3)

	assert first["count"] == 2
	assert second["count"] == 2
	assert registry.is_active("alice", "price_fetch") is True

	registry.start("alice", "price_fetch")
	assert registry.is_active("alice", "price_fetch") is True

	registry.complete("alice", "price_fetch", {"count": 2})
	assert registry.is_active("alice", "price_fetch") is False
