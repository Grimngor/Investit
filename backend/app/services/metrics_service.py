"""Metrics service for tracking application performance and health stats."""

import time
from datetime import UTC, datetime
from typing import Any, Self


class MetricsService:
	"""Singleton service to store and retrieve application metrics in-memory."""

	_instance: Self | None = None

	def __init__(self):
		"""Initialize metrics counters."""
		self.start_time = time.time()
		self.request_count = 0
		self.error_count = 0
		self.latency_sum = 0.0
		self.active_websockets = 0
		self.last_price_fetch: dict[str, Any] = {"timestamp": None, "status": "never", "count": 0}

	@classmethod
	def get_instance(cls) -> Self:
		"""Get or create the singleton instance."""
		if cls._instance is None:
			cls._instance = cls()
		return cls._instance

	def record_request(self, duration: float, status_code: int) -> None:
		"""Record details of a processed HTTP request."""
		self.request_count += 1
		self.latency_sum += duration
		if 500 <= status_code < 600:
			self.error_count += 1

	def record_price_fetch(self, status: str, count: int) -> None:
		"""Record the result of a background price fetch task."""
		self.last_price_fetch = {
			"timestamp": datetime.now(UTC).isoformat(),
			"status": status,
			"count": count,
		}

	def increment_websockets(self) -> None:
		"""Increment active WebSocket connection count."""
		self.active_websockets += 1

	def decrement_websockets(self) -> None:
		"""Decrement active WebSocket connection count."""
		self.active_websockets = max(0, self.active_websockets - 1)

	def get_metrics(self) -> dict[str, Any]:
		"""Return a dictionary of all current metrics."""
		avg_latency = self.latency_sum / self.request_count if self.request_count > 0 else 0.0
		uptime = time.time() - self.start_time
		return {
			"request_count": self.request_count,
			"error_count": self.error_count,
			"avg_latency_ms": round(avg_latency * 1000, 2),
			"active_websockets": self.active_websockets,
			"last_price_fetch": self.last_price_fetch,
			"uptime_seconds": int(uptime),
		}


# Global instance for easy access
metrics = MetricsService.get_instance()
