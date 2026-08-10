"""
Sales Engine - Main Application
Automated sales management system for the Autonomous Company OS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from datetime import datetime
import os

from app.config import settings
from app.database import init_db
from app.routers import leads, pipeline, crm, proposals, analytics
from app.middleware.tenant import tenant_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Sales Engine...")
    
    # Initialize database
    await init_db()
    
    logger.info("Sales Engine started successfully")
    yield
    
    logger.info("Shutting down Sales Engine...")


# Create FastAPI application
app = FastAPI(
    title="Sales Engine",
    description="Automated sales management system for the Autonomous Company OS",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware for multi-tenancy support
app.middleware("http")(tenant_middleware)

# Include routers
app.include_router(leads.router, prefix="/leads", tags=["leads"])
app.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
app.include_router(crm.router, prefix="/crm", tags=["crm"])
app.include_router(proposals.router, prefix="/proposals", tags=["proposals"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Sales Engine",
        "version": "1.0.0",
        "status": "operational",
        "description": "Automated sales management system",
        "features": [
            "Lead management",
            "CRM integration",
            "Pipeline tracking",
            "Automated follow-ups",
            "Proposal generation",
            "Contract management",
            "Sales analytics",
            "Activity tracking"
        ],
        "endpoints": {
            "leads": "/leads",
            "pipeline": "/pipeline",
            "crm": "/crm",
            "proposals": "/proposals",
            "analytics": "/analytics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check performed")
    return {
        "status": "healthy",
        "service": "sales-engine",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8041,
        reload=True
    )
