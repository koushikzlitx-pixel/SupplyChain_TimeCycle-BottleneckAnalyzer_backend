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
    pass


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = Field(None, gt=0)
    priority: Optional[str] = None
    status: Optional[OrderStatus] = None


class OrderResponse(OrderBase):
    id: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderWithStages(OrderResponse):
    stage_logs: List["StageLogResponse"] = []

    class Config:
        from_attributes = True