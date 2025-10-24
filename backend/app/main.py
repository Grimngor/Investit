"""Main FastAPI application."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.docs import description, tags_metadata
from app.logger import setup_logging
from app.routers import auth, dashboard, debug, orders, portfolio, websocket

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
		"http://localhost:3000",
		"http://127.0.0.1:5173",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
app.include_router(websocket.router)
app.include_router(debug.router)

logger.info("InvestIt API started successfully")


@app.get("/")
async def root() -> dict[str, str]:
	"""Root endpoint."""
	return {"message": "Welcome to Investit API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check() -> dict[str, str]:
	"""Health check endpoint."""
	return {"status": "healthy"}
