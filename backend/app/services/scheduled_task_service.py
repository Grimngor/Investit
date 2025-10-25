"""Scheduled task management service for Windows Task Scheduler."""

import logging
import platform
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class ScheduledTaskService:
	"""Service for managing Windows scheduled tasks."""

	TASK_NAME = "InvestIt Monthly Price Update"

	@staticmethod
	def is_task_registered() -> bool:
		"""Check if the monthly price update task is registered."""
		if platform.system() != "Windows":
			return False

		try:
			result = subprocess.run(
				["schtasks", "/Query", "/TN", ScheduledTaskService.TASK_NAME],
				capture_output=True,
				text=True,
				timeout=5,
				check=False,
			)
			return result.returncode == 0
		except Exception as e:
			logger.warning(f"Could not check scheduled task status: {e}")
			return False

	@staticmethod
	def register_task(project_root: Path) -> bool:
		"""
		Register the monthly price update scheduled task.

		Args:
			project_root: Root directory of the InvestIt project

		Returns:
			True if successful, False otherwise
		"""
		if platform.system() != "Windows":
			logger.info("Scheduled tasks only supported on Windows")
			return False

		try:
			setup_script = project_root / "scripts" / "setup_monthly_task.ps1"

			if not setup_script.exists():
				logger.warning(f"Setup script not found: {setup_script}")
				return False

			logger.info("Registering monthly scheduled task...")
			result = subprocess.run(
				["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(setup_script)],
				capture_output=True,
				text=True,
				encoding="utf-8",
				errors="replace",
				timeout=30,
				check=False,
			)

			if result.returncode == 0:
				logger.info("Monthly scheduled task registered successfully")
				return True
			else:
				# Clean up error message for logging
				error_msg = result.stderr.strip() if result.stderr else "Unknown error"
				logger.warning(f"Failed to register scheduled task: {error_msg}")
				return False

		except Exception as e:
			logger.error(f"Error registering scheduled task: {e}")
			return False

	@staticmethod
	def ensure_task_registered(project_root: Path) -> None:
		"""
		Ensure the monthly task is registered. Register if not found.

		Args:
			project_root: Root directory of the InvestIt project
		"""
		if not ScheduledTaskService.is_task_registered():
			logger.info("Monthly scheduled task not found - auto-registering...")
			ScheduledTaskService.register_task(project_root)
		else:
			logger.info("Monthly scheduled task already registered")
