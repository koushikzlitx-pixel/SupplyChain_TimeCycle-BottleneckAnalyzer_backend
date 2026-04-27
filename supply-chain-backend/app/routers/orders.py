from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Order, OrderStatus as ModelOrderStatus
from app.schemas import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderWithStages,
    OrderStatus,
)

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order."""
    db_order = Order(
        order_number=order.order_number,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        product_name=order.product_name,
        quantity=order.quantity,
        priority=order.priority,
        status=ModelOrderStatus(order.status.value) if order.status else ModelOrderStatus.PENDING,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    skip: int = 0,
    limit: int = 100,
    status: OrderStatus = None,
    db: Session = Depends(get_db)
):
    """List all orders with optional filtering."""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == ModelOrderStatus(status.value))
    return query.offset(skip).limit(limit).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
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
    db: Session = Depends(get_db)
):
    """Update an existing order."""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(db_order, field, ModelOrderStatus(value.value))
        else:
            setattr(db_order, field, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Delete an order."""
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    db.delete(db_order)
    db.commit()
    return None