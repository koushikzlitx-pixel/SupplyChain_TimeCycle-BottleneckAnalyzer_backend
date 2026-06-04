"""
Analytics Response Schemas

Pydantic models for analytics API responses.
Provides type-safe, OpenAPI-documented response structures for all analytics endpoints.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional, Any


# ── Summary ────────────────────────────────────────────────────────────────────

class AverageDurations(BaseModel):
    total_time: Optional[float] = None
    procurement_time: Optional[float] = None
    processing_time: Optional[float] = None
    dispatch_time_duration: Optional[float] = None
    delivery_time_duration: Optional[float] = None


class SLAAnalysis(BaseModel):
    total_breaches: int
    breach_percentage: float


class SummaryData(BaseModel):
    total_orders: int
    completed_orders: int
    pending_orders: int
    average_durations: AverageDurations
    sla_analysis: SLAAnalysis
    bottleneck_distribution: Dict[str, int]


class SummaryResponse(BaseModel):
    status: str
    data: SummaryData


# ── Bottlenecks ────────────────────────────────────────────────────────────────

class BottleneckStageEntry(BaseModel):
    stage: str
    count: int
    percentage: float


class TopBottleneckOrder(BaseModel):
    order_id: int
    order_number: str
    bottleneck_stage: Optional[str] = None
    total_time: Optional[float] = None


class BottleneckData(BaseModel):
    total_with_bottleneck: int
    bottleneck_stages: List[BottleneckStageEntry]
    top_bottleneck_orders: List[TopBottleneckOrder]


class BottleneckResponse(BaseModel):
    status: str
    data: BottleneckData


# ── SLA Breaches ───────────────────────────────────────────────────────────────

class StageDurations(BaseModel):
    procurement_time: Optional[float] = None
    processing_time: Optional[float] = None
    dispatch_time_duration: Optional[float] = None
    delivery_time_duration: Optional[float] = None


class BreachedOrder(BaseModel):
    order_id: int
    order_number: str
    breached_stage: Optional[str] = None
    total_time: Optional[float] = None
    stage_durations: StageDurations


class SLABreachData(BaseModel):
    total_breaches: int
    breach_percentage: float
    breached_stages: Dict[str, int]
    breached_orders: List[BreachedOrder]


class SLABreachResponse(BaseModel):
    status: str
    data: SLABreachData


# ── Bottleneck Distribution ────────────────────────────────────────────────────

class BottleneckDistributionEntry(BaseModel):
    stage: str
    count: int
    percentage: float


class BottleneckDistributionResponse(BaseModel):
    total_with_bottleneck: int
    distribution: List[BottleneckDistributionEntry]
