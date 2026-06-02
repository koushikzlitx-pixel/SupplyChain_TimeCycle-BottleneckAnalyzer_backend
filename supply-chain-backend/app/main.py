from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime

from app.database import init_db
from app.routers import orders, stage_logs, analytics
from app.utils.sla_detector import get_sla_thresholds

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database tables
    init_db()
    yield
    # Shutdown: cleanup if needed

app = FastAPI(
    title="Supply Chain Time Cycle & Bottleneck Analyzer",
    description="Advanced supply chain analytics platform with SLA monitoring and bottleneck detection",
    version="2.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(stage_logs.router, prefix="/api/stage-logs", tags=["stage-logs"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/")
def root():
    return {"message": "Supply Chain API is running"}


@app.get("/health")
def health_check():
    """Health check endpoint with SLA configuration and server status."""
    return {
        "status": "healthy",
        "version": app.version,
        "timestamp": datetime.utcnow().isoformat(),
        "sla_thresholds_hours": get_sla_thresholds(),
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}