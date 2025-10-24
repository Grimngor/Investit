"""Logging configuration for InvestIt backend."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
APP_LOG = LOGS_DIR / "app.log"
ERROR_LOG = LOGS_DIR / "error.log"


def setup_logging(level: str = "INFO") -> None:
	"""
	Configure logging for the application.

	Args:
		level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
	"""
	log_level = getattr(logging, level.upper(), logging.INFO)

	# Root logger configuration
	root_logger = logging.getLogger()
	root_logger.setLevel(log_level)

	# Clear existing handlers
	root_logger.handlers.clear()

	# Format for log messages
	log_format = logging.Formatter(
		fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)

	# Console handler (stdout) - INFO and above
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setLevel(logging.INFO)
	console_handler.setFormatter(log_format)
	root_logger.addHandler(console_handler)

	# File handler for all logs - rotating, max 10MB, keep 5 backups
	file_handler = RotatingFileHandler(
		APP_LOG,
		maxBytes=10 * 1024 * 1024,  # 10MB
		backupCount=5,
		encoding="utf-8",
	)
	file_handler.setLevel(log_level)
	file_handler.setFormatter(log_format)
	root_logger.addHandler(file_handler)

	# File handler for ERROR and CRITICAL only
	error_handler = RotatingFileHandler(
		ERROR_LOG,
		maxBytes=10 * 1024 * 1024,  # 10MB
		backupCount=5,
		encoding="utf-8",
	)
	error_handler.setLevel(logging.ERROR)
	error_handler.setFormatter(log_format)
	root_logger.addHandler(error_handler)

	# Reduce noise from third-party libraries
	logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
	logging.getLogger("httpx").setLevel(logging.WARNING)
	logging.getLogger("httpcore").setLevel(logging.WARNING)

	logging.info(f"Logging initialized - Level: {level}, App Log: {APP_LOG}, Error Log: {ERROR_LOG}")


def get_logger(name: str) -> logging.Logger:
	"""
	Get a logger instance for a module.

	Args:
		name: Module name (usually __name__)

	Returns:
		Logger instance
	"""
	return logging.getLogger(name)
