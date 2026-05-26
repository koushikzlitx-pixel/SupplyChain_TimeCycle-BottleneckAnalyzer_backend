"""
Analytics API Router

Provides endpoints for querying supply chain analytics:
- Aggregate metrics and summaries
- SLA breach reports
- Bottleneck analysis
- Performance insights
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import Order
from app.schemas import OrderResponse
from app.services.order_service import order_service
from app.services.order_preprocessing import default_preprocessor
from app.utils.sla_detector import get_sla_thresholds

router = APIRouter()


@router.get("/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Get aggregate analytics summary across all orders.
    
    Returns:
        - Total orders
        - SLA breach count and rate
        - Average stage durations
        - Bottleneck distribution
    """
    summary = order_service.get_analytics_summary(db)
    return summary


@router.get("/sla-breaches", response_model=List[OrderResponse])
def get_sla_breaches(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get orders that breached SLA thresholds.
    
    Returns orders sorted by most recent first.
    """
    orders = order_service.get_orders_with_sla_breach(db, limit=limit)
    return orders


@router.get("/bottlenecks/{stage}", response_model=List[OrderResponse])
def get_orders_by_bottleneck(
    stage: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get orders with specific bottleneck stage.
    
    Valid stages: procurement, processing, dispatch, delivery
    
    Returns orders sorted by total time (descending).
    """
    valid_stages = ["procurement", "processing", "dispatch", "delivery"]
    if stage not in valid_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage. Must be one of: {', '.join(valid_stages)}"
        )
    
    orders = order_service.get_orders_by_bottleneck(db, stage=stage, limit=limit)
    return orders


@router.get("/bottleneck-distribution")
def get_bottleneck_distribution(db: Session = Depends(get_db)):
    """
    Get distribution of bottleneck stages across all orders.
    
    Returns count and percentage for each bottleneck stage.
    """
    from sqlalchemy import func
    
    total_orders = db.query(func.count(Order.id)).filter(
        Order.bottleneck_stage.isnot(None)
    ).scalar()
    
    distribution = db.query(
        Order.bottleneck_stage,
        func.count(Order.id).label('count')
    ).filter(
        Order.bottleneck_stage.isnot(None)
    ).group_by(Order.bottleneck_stage).all()
    
    result = []
    for stage, count in distribution:
        percentage = round((count / total_orders * 100), 2) if total_orders > 0 else 0
        result.append({
            "stage": stage,
            "count": count,
            "percentage": percentage
        })
    
    # Sort by count descending
    result.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total_orders_with_bottleneck": total_orders,
        "distribution": result
    }


@router.get("/stage-performance")
def get_stage_performance(db: Session = Depends(get_db)):
    """
    Get performance statistics for each stage.
    
    Returns average, min, max durations for each stage.
    """
    from sqlalchemy import func
    
    stages = {
        "procurement": Order.procurement_time,
        "processing": Order.processing_time,
        "dispatch": Order.dispatch_time,
        "delivery": Order.delivery_time,
        "total": Order.total_time,
    }
    
    performance = {}
    
    for stage_name, stage_column in stages.items():
        stats = db.query(
            func.avg(stage_column).label('average'),
            func.min(stage_column).label('minimum'),
            func.max(stage_column).label('maximum'),
            func.count(stage_column).label('count')
        ).filter(stage_column.isnot(None)).first()
        
        if stats and stats.count > 0:
            performance[stage_name] = {
                "average": round(stats.average, 2) if stats.average else None,
                "minimum": round(stats.minimum, 2) if stats.minimum else None,
                "maximum": round(stats.maximum, 2) if stats.maximum else None,
                "count": stats.count
            }
        else:
            performance[stage_name] = {
                "average": None,
                "minimum": None,
                "maximum": None,
                "count": 0
            }
    
    return performance


@router.get("/sla-thresholds")
def get_current_sla_thresholds():
    """
    Get current SLA threshold configurations.
    
    Returns threshold hours for each stage.
    """
    thresholds = get_sla_thresholds()
    return {
        "thresholds": thresholds,
        "unit": "hours"
    }


@router.get("/order/{order_id}/detailed-analysis")
def get_order_detailed_analysis(order_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive analytics report for a specific order.
    
    Includes:
    - All stage durations
    - Detailed SLA status per stage
    - Bottleneck analysis with percentages
    - Timeline information
    """
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    # Convert order to dict for preprocessing
    order_dict = {
        "id": order.id,
        "order_number": order.order_number,
        "order_placed_at": order.order_placed_at,
        "order_confirmed_at": order.order_confirmed_at,
        "processing_completed_at": order.processing_completed_at,
        "shipped_at": order.shipped_at,
        "delivered_at": order.delivered_at,
    }
    
    # Get detailed analysis
    analysis = default_preprocessor.get_detailed_analysis(order_dict)
    
    return analysis


@router.get("/orders-by-priority")
def get_orders_by_priority(db: Session = Depends(get_db)):
    """
    Get analytics grouped by order priority.
    
    Returns average durations and SLA breach rates per priority level.
    """
    from sqlalchemy import func
    
    priority_stats = db.query(
        Order.priority,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.sla_breach).label('sla_breaches'),
        func.avg(Order.total_time).label('avg_total_time'),
        func.avg(Order.procurement_time).label('avg_procurement'),
        func.avg(Order.processing_time).label('avg_processing'),
        func.avg(Order.dispatch_time).label('avg_dispatch'),
        func.avg(Order.delivery_time).label('avg_delivery')
    ).group_by(Order.priority).all()
    
    result = []
    for stats in priority_stats:
        breach_rate = round((stats.sla_breaches / stats.total_orders * 100), 2) if stats.total_orders > 0 else 0
        
        result.append({
            "priority": stats.priority,
            "total_orders": stats.total_orders,
            "sla_breaches": stats.sla_breaches,
            "sla_breach_rate": breach_rate,
            "average_durations": {
                "total": round(stats.avg_total_time, 2) if stats.avg_total_time else None,
                "procurement": round(stats.avg_procurement, 2) if stats.avg_procurement else None,
                "processing": round(stats.avg_processing, 2) if stats.avg_processing else None,
                "dispatch": round(stats.avg_dispatch, 2) if stats.avg_dispatch else None,
                "delivery": round(stats.avg_delivery, 2) if stats.avg_delivery else None,
            }
        })
    
    return result


@router.get("/top-delayed-orders", response_model=List[OrderResponse])
def get_top_delayed_orders(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get orders with longest total cycle time.
    
    Returns top N orders sorted by total_time (descending).
    """
    orders = db.query(Order).filter(
        Order.total_time.isnot(None)
    ).order_by(Order.total_time.desc()).limit(limit).all()
    
    return orders
