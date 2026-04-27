from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import StageLog, Order, StageType as ModelStageType
from app.schemas import (
    StageLogCreate,
    StageLogUpdate,
    StageLogResponse,
    StageLogWithOrder,
    StageType,
)

router = APIRouter()


@router.post("/", response_model=StageLogResponse, status_code=status.HTTP_201_CREATED)
def create_stage_log(stage_log: StageLogCreate, db: Session = Depends(get_db)):
    """Create a new stage log entry."""
    # Verify order exists
    order = db.query(Order).filter(Order.id == stage_log.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {stage_log.order_id} not found"
        )
    
    db_stage_log = StageLog(
        order_id=stage_log.order_id,
        stage_name=ModelStageType(stage_log.stage_name.value),
        stage_order=stage_log.stage_order,
        status=stage_log.status,
        notes=stage_log.notes,
    )
    db.add(db_stage_log)
    db.commit()
    db.refresh(db_stage_log)
    return db_stage_log


@router.get("/", response_model=List[StageLogResponse])
def list_stage_logs(
    skip: int = 0,
    limit: int = 100,
    order_id: int = None,
    stage_name: StageType = None,
    db: Session = Depends(get_db)
):
    """List all stage logs with optional filtering."""
    query = db.query(StageLog)
    if order_id:
        query = query.filter(StageLog.order_id == order_id)
    if stage_name:
        query = query.filter(StageLog.stage_name == ModelStageType(stage_name.value))
    return query.offset(skip).limit(limit).all()


@router.get("/{stage_log_id}", response_model=StageLogResponse)
def get_stage_log(stage_log_id: int, db: Session = Depends(get_db)):
    """Get a specific stage log by ID."""
    stage_log = db.query(StageLog).filter(StageLog.id == stage_log_id).first()
    if not stage_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stage log with id {stage_log_id} not found"
        )
    return stage_log


@router.get("/order/{order_id}", response_model=List[StageLogResponse])
def get_stage_logs_by_order(order_id: int, db: Session = Depends(get_db)):
    """Get all stage logs for a specific order."""
    # Verify order exists
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    stage_logs = db.query(StageLog).filter(
        StageLog.order_id == order_id
    ).order_by(StageLog.stage_order).all()
    return stage_logs


@router.patch("/{stage_log_id}", response_model=StageLogResponse)
def update_stage_log(
    stage_log_id: int,
    stage_log_update: StageLogUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing stage log."""
    db_stage_log = db.query(StageLog).filter(StageLog.id == stage_log_id).first()
    if not db_stage_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stage log with id {stage_log_id} not found"
        )
    
    update_data = stage_log_update.model_dump(exclude_unset=True)
    
    # Calculate duration if both timestamps are provided
    if update_data.get("completed_at") and db_stage_log.started_at:
        completed = update_data.get("completed_at")
        if isinstance(completed, str):
            completed = datetime.fromisoformat(completed.replace("Z", "+00:00"))
        db_stage_log.duration_seconds = (completed - db_stage_log.started_at).total_seconds()
    
    for field, value in update_data.items():
        setattr(db_stage_log, field, value)
    
    db.commit()
    db.refresh(db_stage_log)
    return db_stage_log


@router.delete("/{stage_log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stage_log(stage_log_id: int, db: Session = Depends(get_db)):
    """Delete a stage log."""
    db_stage_log = db.query(StageLog).filter(StageLog.id == stage_log_id).first()
    if not db_stage_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stage log with id {stage_log_id} not found"
        )
    db.delete(db_stage_log)
    db.commit()
    return None