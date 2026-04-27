"""Main FastAPI application."""

import logging
import os
import platform
import sys
import time
from datetime import UTC, datetime
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
	instruments,
	orders,
	portfolio,
	websocket,
)
from app.routers import (
	prices as prices_router,
)
from app.services.metrics_service import metrics

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
app.include_router(instruments.router)
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
	"""Run on application startup."""
	logger.info("InvestIt API started successfully")


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
