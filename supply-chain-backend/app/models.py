from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base):
    """Order table - stores core order information."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    priority = Column(String(20), default="normal")  # normal, high, urgent
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    stage_logs = relationship("StageLog", back_populates="order", cascade="all, delete-orphan")


class StageType(str, enum.Enum):
    ORDER_PLACED = "order_placed"
    ORDER_CONFIRMED = "order_confirmed"
    PROCESSING = "processing"
    QUALITY_CHECK = "quality_check"
    PACKAGING = "packaging"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"


class StageLog(Base):
    """StageLog table - tracks stage-wise progression of orders."""
    __tablename__ = "stage_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_name = Column(Enum(StageType), nullable=False, index=True)
    stage_order = Column(Integer, nullable=False)  # Sequence number of the stage
    status = Column(String(50), default="pending", nullable=False)  # pending, in_progress, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)  # Time spent in this stage (seconds)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="stage_logs")


class BottleneckAnalysis(Base):
    """BottleneckAnalysis table - stores identified bottlenecks."""
    __tablename__ = "bottleneck_analysis"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_name = Column(Enum(StageType), nullable=False)
    average_duration_seconds = Column(Float, nullable=True)
    threshold_seconds = Column(Float, nullable=False)
    actual_duration_seconds = Column(Float, nullable=True)
    is_bottleneck = Column(Integer, default=0)  # 0 = no, 1 = yes
    analysis_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)