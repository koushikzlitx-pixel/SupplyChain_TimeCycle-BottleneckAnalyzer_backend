from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class StageType(str, Enum):
    ORDER_PLACED = "order_placed"
    ORDER_CONFIRMED = "order_confirmed"
    PROCESSING = "processing"
    QUALITY_CHECK = "quality_check"
    PACKAGING = "packaging"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"


# Schemas for StageLog
class StageLogBase(BaseModel):
    order_id: int = Field(..., gt=0)
    stage_name: StageType
    stage_order: int = Field(..., ge=0)
    status: str = Field(default="pending", max_length=50)
    notes: Optional[str] = None


class StageLogCreate(StageLogBase):
    pass


class StageLogUpdate(BaseModel):
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class StageLogResponse(StageLogBase):
    id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StageLogWithOrder(StageLogResponse):
    order: Optional["OrderBrief"] = None

    class Config:
        from_attributes = True


class OrderBrief(BaseModel):
    id: int
    order_number: str
    customer_name: str

    class Config:
        from_attributes = True


# Update forward references
StageLogResponse.model_rebuild()
OrderWithStages.model_rebuild()
StageLogWithOrder.model_rebuild()