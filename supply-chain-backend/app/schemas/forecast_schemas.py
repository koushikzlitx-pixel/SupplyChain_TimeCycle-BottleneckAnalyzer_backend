"""
Forecast Pydantic Schemas

Request and response models for the demand forecasting API.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# ── Demand Record ──────────────────────────────────────────────────────────────

class DemandRecordCreate(BaseModel):
    product_id: str = Field(..., max_length=100)
    product_name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    record_date: datetime
    quantity_sold: float = Field(..., ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    inventory_level: Optional[float] = Field(None, ge=0)


class DemandRecordResponse(DemandRecordCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Training ───────────────────────────────────────────────────────────────────

class TrainModelRequest(BaseModel):
    product_id: str = Field(..., max_length=100)


class ModelMetrics(BaseModel):
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    mape: float = Field(..., description="Mean Absolute Percentage Error (%)")


class TrainModelResponse(BaseModel):
    product_id: str
    status: str
    training_records: int
    test_records: int
    metrics: ModelMetrics
    feature_importance: Dict[str, float]
    trained_at: str


# ── Prediction ─────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    product_id: str = Field(..., max_length=100)
    horizon_days: int = Field(default=30, ge=1, le=365)


class DailyForecast(BaseModel):
    date: str
    predicted_demand: float
    confidence_lower: float
    confidence_upper: float


class PredictResponse(BaseModel):
    product_id: str
    horizon_days: int
    forecasts: List[DailyForecast]
    model_trained_at: Optional[str] = None
    total_predicted_demand: float


# ── Model Info ─────────────────────────────────────────────────────────────────

class ModelInfo(BaseModel):
    product_id: str
    status: str
    trained_at: Optional[str] = None
    training_records: Optional[int] = None
    metrics: Optional[ModelMetrics] = None


# ── Dummy Data Generation ──────────────────────────────────────────────────────

class GenerateDemandDataRequest(BaseModel):
    product_id: str = Field(..., max_length=100)
    product_name: str = Field(..., max_length=255)
    category: Optional[str] = Field(default="general", max_length=100)
    days: int = Field(default=365, ge=90, le=730)
    base_demand: Optional[float] = Field(default=None, ge=1, le=10000)


class GenerateDemandDataResponse(BaseModel):
    product_id: str
    records_created: int
    date_range_start: str
    date_range_end: str
