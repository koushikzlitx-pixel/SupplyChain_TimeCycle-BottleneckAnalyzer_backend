from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Order, OrderStatus as ModelOrderStatus
from app.schemas import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderWithStages,
    OrderStatus,
)
from app.services.order_service import order_service

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    Create a new order with automatic analytics preprocessing.
    
    The order will be processed through the analytics pipeline to calculate:
    - Stage durations (procurement, processing, dispatch, delivery)
    - SLA breach detection
    - Bottleneck identification
    """
    # Convert Pydantic model to dict for service layer
    order_data = order.model_dump()
    
    # Handle status enum conversion
    if order.status:
        order_data["status"] = ModelOrderStatus(order.status.value)
    else:
        order_data["status"] = ModelOrderStatus.PENDING
    
    # Create order through service layer (includes preprocessing)
    db_order = order_service.create_order(db, order_data)
    
    return db_order


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=1000),
    status: OrderStatus = None,
    sla_breach: bool = None,
    bottleneck_stage: str = None,
    from_date: Optional[datetime] = Query(default=None, description="Filter by order_placed_at >= date (ISO 8601)"),
    to_date: Optional[datetime] = Query(default=None, description="Filter by order_placed_at <= date (ISO 8601)"),
    db: Session = Depends(get_db)
):
    """
    List all orders with optional filtering.
    
    Supports filtering by:
    - status: Order status (pending, processing, completed, cancelled)
    - sla_breach: Whether order breached SLA (true/false)
    - bottleneck_stage: Specific bottleneck stage
    - from_date / to_date: Date range on order_placed_at (ISO 8601)
    """
    model_status = ModelOrderStatus(status.value) if status else None
    
    orders = order_service.list_orders(
        db=db,
        skip=skip,
        limit=limit,
        status=model_status,
        sla_breach=sla_breach,
        bottleneck_stage=bottleneck_stage,
        from_date=from_date,
        to_date=to_date,
    )
    
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order by ID with all analytics fields."""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    return order


@router.get("/{order_id}/stages", response_model=OrderWithStages)
def get_order_with_stages(order_id: int, db: Session = Depends(get_db)):
    """Get order with all stage logs."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    return order


@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    reprocess_analytics: bool = True,
    db: Session = Depends(get_db)
):
    """
    Update an existing order with optional analytics reprocessing.
    
    Args:
        order_id: Order ID to update
        order_update: Fields to update
        reprocess_analytics: Whether to recalculate analytics (default: true)
    
    If reprocess_analytics=true, all durations, SLA status, and bottleneck
    will be recalculated based on the updated timestamps.
    """
    update_data = order_update.model_dump(exclude_unset=True)
    
    # Handle status enum conversion
    if "status" in update_data and update_data["status"]:
        update_data["status"] = ModelOrderStatus(update_data["status"].value)
    
    # Update through service layer
    db_order = order_service.update_order(
        db=db,
        order_id=order_id,
        update_data=update_data,
        reprocess_analytics=reprocess_analytics
    )
    
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    return db_order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Delete an order and all associated data."""
    deleted = order_service.delete_order(db, order_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    return None