"""
Demand Forecast Service

Core ML service for training, saving, loading, and running inference on
demand forecasting models. Uses RandomForestRegressor as the primary estimator
with time-series feature engineering.

Model files are persisted under models/forecast/ using joblib.
"""

import os
import re
import random
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.models import DemandRecord, ForecastPrediction
from app.utils.forecast_utils import (
    FEATURE_COLUMNS,
    build_future_feature_row,
    engineer_features,
)

# Directory for persisted model files (relative to working directory)
MODEL_DIR = Path("models/forecast")
MIN_TRAINING_RECORDS = 30


def _safe_product_id(product_id: str) -> str:
    """Sanitize product_id for use in file names."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", product_id)


def _model_path(product_id: str) -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    return MODEL_DIR / f"demand_model_{_safe_product_id(product_id)}.pkl"


class ForecastService:
    """
    Manages the full lifecycle of demand forecasting models:
    - Training on historical DemandRecord data
    - Persisting trained models to disk with joblib
    - Loading models for inference
    - Generating multi-day forecasts
    - Seeding synthetic demand data for testing
    """

    # ── Training ───────────────────────────────────────────────────────────────

    def train_model(self, db: Session, product_id: str) -> Dict[str, Any]:
        """
        Train a RandomForest demand forecasting model for a product.

        Requires at least MIN_TRAINING_RECORDS demand records in the database.

        Returns training metrics and feature importances.
        """
        records = (
            db.query(DemandRecord)
            .filter(DemandRecord.product_id == product_id)
            .order_by(DemandRecord.record_date)
            .all()
        )

        if len(records) < MIN_TRAINING_RECORDS:
            raise ValueError(
                f"Need at least {MIN_TRAINING_RECORDS} demand records to train. "
                f"Found {len(records)} for product '{product_id}'."
            )

        # Build DataFrame
        df = pd.DataFrame(
            [{"date": r.record_date, "demand": r.quantity_sold} for r in records]
        )

        # Feature engineering
        df = engineer_features(df)
        df = df.dropna(subset=FEATURE_COLUMNS)

        X = df[FEATURE_COLUMNS].values
        y = df["demand"].values

        # Time-ordered 80/20 split
        split = max(1, int(len(df) * 0.8))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        # Choose estimator based on data volume
        if len(X_train) >= 60:
            model = RandomForestRegressor(
                n_estimators=150, max_depth=12, random_state=42, n_jobs=-1
            )
        else:
            model = LinearRegression()

        model.fit(X_train, y_train)

        # Evaluation
        y_pred = model.predict(X_test) if len(X_test) > 0 else model.predict(X_train)
        y_true = y_test if len(X_test) > 0 else y_train

        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mape = float(
            np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-9))) * 100
        )

        # Feature importance (RF only; zeros for linear)
        if hasattr(model, "feature_importances_"):
            importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_.tolist()))
        else:
            importances = {col: 0.0 for col in FEATURE_COLUMNS}

        trained_at = datetime.utcnow().isoformat()

        # Persist model + metadata
        model_data = {
            "model": model,
            "product_id": product_id,
            "trained_at": trained_at,
            "training_records": len(df),
            "metrics": {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 2)},
            "feature_columns": FEATURE_COLUMNS,
            "base_date": df["date"].min(),
            "last_date": df["date"].max(),
            "demand_tail": df["demand"].tail(30).tolist(),
        }
        joblib.dump(model_data, _model_path(product_id))

        return {
            "product_id": product_id,
            "status": "trained",
            "training_records": len(X_train),
            "test_records": len(X_test),
            "metrics": {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 2)},
            "feature_importance": {
                k: round(v, 4)
                for k, v in sorted(importances.items(), key=lambda x: -x[1])
            },
            "trained_at": trained_at,
        }

    # ── Inference ──────────────────────────────────────────────────────────────

    def predict(
        self, db: Session, product_id: str, horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a multi-day demand forecast for a product.

        Args:
            db: Database session (used to persist predictions).
            product_id: Target product.
            horizon_days: Number of days ahead to forecast.

        Returns:
            dict with forecasts list and summary stats.
        """
        path = _model_path(product_id)
        if not path.exists():
            raise FileNotFoundError(
                f"No trained model found for product '{product_id}'. Train first."
            )

        model_data = joblib.load(path)
        model = model_data["model"]
        base_date: datetime = model_data["base_date"]
        last_date: datetime = model_data["last_date"]
        demand_history: List[float] = list(model_data["demand_tail"])
        trained_at: str = model_data.get("trained_at")

        forecasts = []
        # Delete previous predictions for this product before storing new batch
        db.query(ForecastPrediction).filter(
            ForecastPrediction.product_id == product_id
        ).delete()

        for i in range(horizon_days):
            future_date = last_date + timedelta(days=i + 1)
            features = [
                build_future_feature_row(future_date, base_date, demand_history)
            ]

            predicted = float(max(0.0, model.predict(features)[0]))

            # Confidence band: ±1.96 × rolling_std of recent history
            recent_std = float(np.std(demand_history[-7:])) if len(demand_history) >= 2 else predicted * 0.1
            lower = round(max(0.0, predicted - 1.96 * recent_std), 2)
            upper = round(predicted + 1.96 * recent_std, 2)
            predicted = round(predicted, 2)

            forecasts.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "predicted_demand": predicted,
                "confidence_lower": lower,
                "confidence_upper": upper,
            })

            # Store to DB
            db.add(ForecastPrediction(
                product_id=product_id,
                forecast_date=future_date,
                predicted_demand=predicted,
                confidence_lower=lower,
                confidence_upper=upper,
                model_version=trained_at,
                horizon_days=horizon_days,
            ))

            demand_history.append(predicted)

        db.commit()

        return {
            "product_id": product_id,
            "horizon_days": horizon_days,
            "forecasts": forecasts,
            "model_trained_at": trained_at,
            "total_predicted_demand": round(sum(f["predicted_demand"] for f in forecasts), 2),
        }

    # ── Model Management ───────────────────────────────────────────────────────

    def get_model_info(self, product_id: str) -> Dict[str, Any]:
        """Return metadata for a trained model, or status=not_trained."""
        path = _model_path(product_id)
        if not path.exists():
            return {"product_id": product_id, "status": "not_trained"}

        md = joblib.load(path)
        return {
            "product_id": product_id,
            "status": "trained",
            "trained_at": md.get("trained_at"),
            "training_records": md.get("training_records"),
            "metrics": md.get("metrics"),
        }

    def list_trained_models(self) -> List[Dict[str, Any]]:
        """List all persisted model files with metadata."""
        if not MODEL_DIR.exists():
            return []

        result = []
        for f in MODEL_DIR.glob("demand_model_*.pkl"):
            try:
                md = joblib.load(f)
                result.append({
                    "product_id": md.get("product_id"),
                    "trained_at": md.get("trained_at"),
                    "training_records": md.get("training_records"),
                    "metrics": md.get("metrics"),
                })
            except Exception:
                pass
        return result

    def delete_model(self, product_id: str) -> bool:
        """Delete a persisted model file. Returns True if deleted."""
        path = _model_path(product_id)
        if path.exists():
            path.unlink()
            return True
        return False

    # ── Synthetic Data Generation ──────────────────────────────────────────────

    def generate_demand_records(
        self,
        db: Session,
        product_id: str,
        product_name: str,
        category: str = "general",
        days: int = 365,
        base_demand: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Insert synthetic daily demand records for testing.

        Simulates trend, weekly seasonality, monthly seasonality, and Gaussian noise.
        """
        if base_demand is None:
            base_demand = random.uniform(50.0, 200.0)

        trend_rate = random.uniform(-0.05, 0.25)
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)

        # Remove existing records for this product
        db.query(DemandRecord).filter(DemandRecord.product_id == product_id).delete()

        records = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            trend = base_demand * (1 + trend_rate * i / days)
            weekly = 1.0 + 0.20 * np.sin(2 * np.pi * date.weekday() / 7)
            monthly = 1.0 + 0.30 * np.sin(2 * np.pi * date.month / 12)
            noise = random.gauss(0, base_demand * 0.08)
            qty = max(0.0, trend * weekly * monthly + noise)

            records.append(DemandRecord(
                product_id=product_id,
                product_name=product_name,
                category=category,
                record_date=date,
                quantity_sold=round(qty, 2),
                revenue=round(qty * random.uniform(5.0, 50.0), 2),
                inventory_level=round(random.uniform(qty * 1.5, qty * 4.0), 2),
            ))

        db.bulk_save_objects(records)
        db.commit()

        return {
            "product_id": product_id,
            "records_created": days,
            "date_range_start": start_date.strftime("%Y-%m-%d"),
            "date_range_end": (start_date + timedelta(days=days - 1)).strftime("%Y-%m-%d"),
        }


# Singleton
forecast_service = ForecastService()
