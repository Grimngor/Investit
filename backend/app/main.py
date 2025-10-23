"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.docs import tags_metadata, description
from app.routers import auth, portfolio, websocket, debug

# Create FastAPI app
app = FastAPI(title="Investit API", description=description, version="1.0.0", openapi_tags=tags_metadata)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(websocket.router)
app.include_router(debug.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Investit API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
