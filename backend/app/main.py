"""Main FastAPI application."""

import asyncio
import logging
import os
import platform
import sys
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.docs import description, tags_metadata
from app.logger import setup_logging
from app.routers import (
	auth,
	dashboard,
	debug,
	orders,
	portfolio,
	websocket,
)
from app.routers import (
	prices as prices_router,
)
from app.services.metrics_service import metrics
from app.services.price_service import PriceService
from app.services.scheduled_task_service import ScheduledTaskService
from app.services.storage_service import StorageService

# Initialize logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
setup_logging(level=LOG_LEVEL)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
	title="Investit API",
	description=description,
	version="1.0.0",
	openapi_tags=tags_metadata,
)
# Background tasks set to prevent garbage collection
background_tasks = set()


# Configure CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:5173",
		"http://localhost:5174",
		"http://localhost:3000",
		"http://127.0.0.1:5173",
		"http://127.0.0.1:5174",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(orders.router)
app.include_router(prices_router.router)
app.include_router(dashboard.router)
app.include_router(websocket.router)
app.include_router(debug.router)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
	"""Middleware to track request latency and error rates."""
	start_time = time.time()
	response = await call_next(request)
	process_time = time.time() - start_time
	metrics.record_request(process_time, response.status_code)
	return response


@app.on_event("startup")
async def startup_event():
	"""Run on application startup - check for stale prices and auto-fetch if needed."""
	logger.info("InvestIt API started successfully")

	# Auto-register scheduled task for monthly price updates
	try:
		project_root = settings.DATA_DIR.parent
		ScheduledTaskService.ensure_task_registered(project_root)
	except Exception as e:
		logger.warning(f"Could not register scheduled task (non-Windows or missing script?): {e}")

	# Check if we need to refresh prices
	try:
		users_file = settings.DATA_DIR / "users.json"
		if not users_file.exists():
			logger.info("No users.json file found - skipping price check")
			return

		users = StorageService.load_json(users_file, default={})
		stale_threshold = timedelta(days=14)  # 2 weeks

		# Check all users for stale prices
		for username, user_data in users.items():
			if not user_data.get("orders"):
				continue

			prices = user_data.get("prices", {})
			if not prices:
				logger.info(f"No prices cached for user {username} - will fetch on first request")
				continue

			# Find oldest price timestamp
			oldest_timestamp = None
			for price_data in prices.values():
				timestamp_str = price_data.get("timestamp", "")
				if timestamp_str and (oldest_timestamp is None or timestamp_str < oldest_timestamp):
					oldest_timestamp = timestamp_str

			if oldest_timestamp:
				try:
					oldest_dt = datetime.fromisoformat(oldest_timestamp.replace("Z", "+00:00"))
					age = datetime.now(UTC) - oldest_dt

					if age > stale_threshold:
						logger.info(f"Prices for {username} are {age.days} days old - triggering background fetch")

						# Get ISINs from finalized orders
						orders = user_data.get("orders", [])
						finalized_orders = [o for o in orders if o.get("status", "").lower() == "finalizada"]
						unique_isins = list(set(o.get("isin") for o in finalized_orders if o.get("isin")))

						if unique_isins:
							# Trigger background fetch asynchronously
							task = asyncio.create_task(PriceService.fetch_and_update_prices(username, unique_isins))
							background_tasks.add(task)
							task.add_done_callback(background_tasks.discard)
							logger.info(f"Started background price fetch for {len(unique_isins)} instruments ({username})")
				except Exception as e:
					logger.warning(f"Could not parse timestamp for {username}: {e}")

	except Exception as e:
		logger.error(f"Error during startup price check: {e}")


@app.get("/")
async def root() -> dict[str, str]:
	"""Root endpoint."""
	return {"message": "Welcome to Investit API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check() -> dict[str, Any]:
	"""Enhanced health check endpoint with system info and metrics."""
	# Check storage writability
	storage_ok = False
	try:
		test_file = settings.DATA_DIR / ".health_check"
		test_file.write_text("ok")
		test_file.unlink()
		storage_ok = True
	except Exception:
		storage_ok = False

	return {
		"status": "healthy" if storage_ok else "unhealthy",
		"timestamp": datetime.now(UTC).isoformat(),
		"system": {
			"python": sys.version.split()[0],
			"os": platform.system(),
			"cpus": os.cpu_count(),
		},
		"storage": {"writable": storage_ok},
		"metrics": metrics.get_metrics(),
	}
