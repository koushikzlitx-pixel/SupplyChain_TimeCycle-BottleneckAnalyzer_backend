from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import orders, stage_logs, analytics

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
    return {"status": "healthy"}