"""
Forecasting API Router

Exposes demand forecasting endpoints:
- Seed historical demand data
- Train forecasting models
- Run predictions / retrieve stored forecasts
- Model management (info, list, delete)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import DemandRecord, ForecastPrediction
from app.schemas.forecast_schemas import (
    DemandRecordCreate,
    DemandRecordResponse,
    GenerateDemandDataRequest,
    GenerateDemandDataResponse,
    ModelInfo,
    PredictResponse,
    TrainModelRequest,
    TrainModelResponse,
)
from app.services.forecast_service import forecast_service

router = APIRouter()


# ── Demand Data ────────────────────────────────────────────────────────────────

@router.post("/demand-data", response_model=DemandRecordResponse, status_code=status.HTTP_201_CREATED)
def add_demand_record(record: DemandRecordCreate, db: Session = Depends(get_db)):
    """Insert a single historical demand record."""
    db_record = DemandRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/demand-data/{product_id}", response_model=List[DemandRecordResponse])
def get_demand_records(
    product_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Retrieve historical demand records for a product."""
    return (
        db.query(DemandRecord)
        .filter(DemandRecord.product_id == product_id)
        .order_by(DemandRecord.record_date.desc())
        .limit(limit)
        .all()
    )


@router.post("/generate-demand-data", response_model=GenerateDemandDataResponse)
def generate_demand_data(request: GenerateDemandDataRequest, db: Session = Depends(get_db)):
    """
    Generate synthetic daily demand records for a product.

    Simulates trend, weekly seasonality, monthly seasonality, and noise.
    Useful for testing the forecasting pipeline without real data.
    """
    try:
        result = forecast_service.generate_demand_records(
            db=db,
            product_id=request.product_id,
            product_name=request.product_name,
            category=request.category or "general",
            days=request.days,
            base_demand=request.base_demand,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate demand data: {str(e)}",
        )


# ── Model Training ─────────────────────────────────────────────────────────────

@router.post("/train", response_model=TrainModelResponse)
def train_forecast_model(request: TrainModelRequest, db: Session = Depends(get_db)):
    """
    Train a RandomForest demand forecasting model for a product.

    Requires at least 30 historical demand records in the database.
    Persists the trained model to disk for later inference.

    Returns training metrics (MAE, RMSE, MAPE) and feature importances.
    """
    try:
        result = forecast_service.train_model(db=db, product_id=request.product_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}",
        )


# ── Predictions ────────────────────────────────────────────────────────────────

@router.get("/predict/{product_id}", response_model=PredictResponse)
def predict_demand(
    product_id: str,
    horizon_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Generate a multi-day demand forecast for a product.

    Requires a trained model (call /train first).
    Stores predictions in the database and returns the full forecast series
    with confidence intervals.
    """
    try:
        result = forecast_service.predict(db=db, product_id=product_id, horizon_days=horizon_days)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.get("/predictions/{product_id}")
def get_stored_predictions(
    product_id: str,
    limit: int = Query(default=365, ge=1, le=730),
    db: Session = Depends(get_db),
):
    """Retrieve stored forecast predictions for a product from the database."""
    predictions = (
        db.query(ForecastPrediction)
        .filter(ForecastPrediction.product_id == product_id)
        .order_by(ForecastPrediction.forecast_date.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "date": p.forecast_date.strftime("%Y-%m-%d"),
            "predicted_demand": p.predicted_demand,
            "confidence_lower": p.confidence_lower,
            "confidence_upper": p.confidence_upper,
            "model_version": p.model_version,
        }
        for p in predictions
    ]


# ── Model Management ───────────────────────────────────────────────────────────

@router.get("/models", response_model=List[ModelInfo])
def list_models():
    """List all trained forecasting models with metadata and metrics."""
    return forecast_service.list_trained_models()


@router.get("/models/{product_id}", response_model=ModelInfo)
def get_model_info(product_id: str):
    """Get training metadata and evaluation metrics for a specific product model."""
    return forecast_service.get_model_info(product_id)


@router.delete("/models/{product_id}")
def delete_model(product_id: str, db: Session = Depends(get_db)):
    """
    Delete the trained model file for a product.

    Also clears stored predictions for that product from the database.
    """
    deleted = forecast_service.delete_model(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No trained model found for product '{product_id}'.",
        )
    # Clear stored predictions
    db.query(ForecastPrediction).filter(ForecastPrediction.product_id == product_id).delete()
    db.commit()
    return {"status": "deleted", "product_id": product_id}


# ── Full Pipeline (convenience) ────────────────────────────────────────────────

@router.post("/pipeline/{product_id}")
def run_full_pipeline(
    product_id: str,
    horizon_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Run the complete forecasting pipeline in one call:
    1. Train the model on stored demand records.
    2. Generate and store predictions for horizon_days.

    Returns combined training metrics and forecast series.
    """
    try:
        train_result = forecast_service.train_model(db=db, product_id=product_id)
        predict_result = forecast_service.predict(db=db, product_id=product_id, horizon_days=horizon_days)
        return {
            "status": "success",
            "training": train_result,
            "forecast": predict_result,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {str(e)}",
        )
