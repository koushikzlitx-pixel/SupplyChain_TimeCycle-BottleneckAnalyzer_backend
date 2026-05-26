from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Schemas for Order
class OrderBase(BaseModel):
    order_number: str = Field(..., max_length=50)
    customer_name: str = Field(..., max_length=255)
    customer_email: Optional[EmailStr] = None
    product_name: str = Field(..., max_length=255)
    quantity: int = Field(..., gt=0)
    priority: str = Field(default="normal", max_length=20)


class OrderCreate(OrderBase):
    """Schema for creating orders with optional lifecycle timestamps."""
    # Optional lifecycle timestamps
    order_placed_at: Optional[datetime] = None
    order_confirmed_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    status: Optional[OrderStatus] = None


class OrderUpdate(BaseModel):
    """Schema for updating orders with optional lifecycle timestamps."""
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = Field(None, gt=0)
    priority: Optional[str] = None
    status: Optional[OrderStatus] = None
    
    # Lifecycle timestamps
    order_placed_at: Optional[datetime] = None
    order_confirmed_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class OrderResponse(OrderBase):
    """Schema for order responses with all analytics fields."""
    id: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Lifecycle timestamps
    order_placed_at: Optional[datetime] = None
    order_confirmed_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Analytics fields - Durations
    procurement_time: Optional[float] = None
    processing_time: Optional[float] = None
    dispatch_time: Optional[float] = None
    delivery_time: Optional[float] = None
    total_time: Optional[float] = None
    
    # Analytics fields - SLA breach
    sla_breach: bool = False
    breached_stage: Optional[str] = None
    
    # Analytics fields - Bottleneck
    bottleneck_stage: Optional[str] = None

    class Config:
        from_attributes = True


class OrderWithStages(OrderResponse):
    stage_logs: List["StageLogResponse"] = []

    class Config:
        from_attributes = True