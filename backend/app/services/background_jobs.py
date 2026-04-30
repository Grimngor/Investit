"""In-process background job registry for lightweight provider tasks."""

from datetime import UTC, datetime
from typing import Any


class BackgroundJobRegistry:
	"""Track lightweight background jobs by user and job type."""

	_ACTIVE_STATES = {"queued", "running"}

	def __init__(self) -> None:
		"""Initialize the in-memory job state store."""
		self._jobs: dict[tuple[str, str], dict[str, Any]] = {}

	def get(self, username: str, job_type: str) -> dict[str, Any] | None:
		"""Return the current job state for a user and job type."""
		job = self._jobs.get((username, job_type))
		return dict(job) if job else None

	def is_active(self, username: str, job_type: str) -> bool:
		"""Return True when a job is queued or running."""
		job = self.get(username, job_type)
		return bool(job and job.get("state") in self._ACTIVE_STATES)

	def queue(self, username: str, job_type: str, count: int = 0) -> dict[str, Any]:
		"""Mark a job as queued unless one is already active."""
		existing = self.get(username, job_type)
		if existing and existing.get("state") in self._ACTIVE_STATES:
			return existing

		job = {
			"username": username,
			"job_type": job_type,
			"state": "queued",
			"count": count,
			"queued_at": datetime.now(UTC).isoformat(),
			"started_at": None,
			"completed_at": None,
			"error": None,
		}
		self._jobs[(username, job_type)] = job
		return dict(job)

	def start(self, username: str, job_type: str) -> dict[str, Any]:
		"""Mark a queued job as running."""
		job = self._jobs.setdefault((username, job_type), {"username": username, "job_type": job_type})
		job.update({"state": "running", "started_at": datetime.now(UTC).isoformat(), "error": None})
		return dict(job)

	def complete(self, username: str, job_type: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
		"""Mark a job as completed and store its result."""
		job = self._jobs.setdefault((username, job_type), {"username": username, "job_type": job_type})
		job.update({"state": "completed", "completed_at": datetime.now(UTC).isoformat(), "error": None, "result": result or {}})
		return dict(job)

	def fail(self, username: str, job_type: str, error: str) -> dict[str, Any]:
		"""Mark a job as failed and store the failure message."""
		job = self._jobs.setdefault((username, job_type), {"username": username, "job_type": job_type})
		job.update({"state": "failed", "completed_at": datetime.now(UTC).isoformat(), "error": error})
		return dict(job)

	def clear(self) -> None:
		"""Clear all tracked job state."""
		self._jobs.clear()


background_jobs = BackgroundJobRegistry()
