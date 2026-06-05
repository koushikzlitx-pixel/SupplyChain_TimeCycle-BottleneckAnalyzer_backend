"""
Analytics API Router

Provides endpoints for querying supply chain analytics:
- Aggregate metrics and summaries
- SLA breach reports
- Bottleneck analysis
- Performance insights
- CSV export workflows
- Dummy data generation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import Order
from app.schemas import OrderResponse, SummaryResponse, BottleneckResponse, SLABreachResponse, BottleneckDistributionResponse
from app.services.order_service import order_service
from app.services.order_preprocessing import default_preprocessor
from app.services.analytics_service import analytics_service
from app.services.export_service import export_service
from app.services.dummy_data_generator import dummy_data_generator
from app.utils.sla_detector import get_sla_thresholds

router = APIRouter()


# ==================== ENHANCED SUMMARY & ANALYTICS ====================

@router.get("/summary-enhanced")
def get_enhanced_summary(db: Session = Depends(get_db)):
    """
    Get comprehensive enhanced analytics summary.
    
    Uses optimized aggregation queries for performance.
    """
    summary = analytics_service.get_summary_analytics(db)
    return summary


@router.get("/bottlenecks-enhanced")
def get_enhanced_bottleneck_analysis(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get detailed bottleneck analysis with top orders.
    
    Returns:
    - Total orders with bottlenecks
    - Distribution by stage
    - Top slowest orders
    """
    analysis = analytics_service.get_bottleneck_analytics(db, limit=limit)
    return analysis


@router.get("/sla-breaches-enhanced")
def get_enhanced_sla_analysis(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get detailed SLA breach analysis.
    
    Returns:
    - Total breaches and percentage
    - Breached stages distribution
    - Detailed breached orders with stage durations
    """
    analysis = analytics_service.get_sla_breach_analytics(db, limit=limit)
    return analysis


@router.get("/stage-performance-enhanced")
def get_stage_performance_metrics(db: Session = Depends(get_db)):
    """
    Get comprehensive stage performance metrics.
    
    Returns min, max, avg, and standard deviation for each stage.
    """
    metrics = analytics_service.get_stage_performance_metrics(db)
    return metrics


@router.get("/summary", response_model=SummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Get aggregate analytics summary across all orders.
    
    Returns:
        - Total orders
        - SLA breach count and rate
        - Average stage durations
        - Bottleneck distribution
    """
    try:
        return analytics_service.get_summary_response(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics summary: {str(e)}"
        )


@router.get("/bottlenecks", response_model=BottleneckResponse)
def get_bottlenecks(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get bottleneck stage distribution and top affected orders.
    """
    try:
        return analytics_service.get_bottleneck_response(db, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch bottleneck analytics: {str(e)}"
        )


@router.get("/sla-breaches", response_model=SLABreachResponse)
def get_sla_breaches(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get orders that breached SLA thresholds.
    
    Returns orders sorted by most recent first.
    """
    try:
        return analytics_service.get_sla_breach_response(db, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch SLA breach analytics: {str(e)}"
        )


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
        "dispatch": Order.dispatch_time_duration,
        "delivery": Order.delivery_time_duration,
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
        func.avg(Order.dispatch_time_duration).label('avg_dispatch'),
        func.avg(Order.delivery_time_duration).label('avg_delivery')
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


# ==================== CSV EXPORT ====================

@router.get("/export")
def export_orders_csv(db: Session = Depends(get_db)):
    """
    Export all analytics-ready orders to CSV file.
    
    Returns:
        - Export path
        - Export summary with statistics
        - File location for download
    """
    try:
        # Fetch orders for export
        orders_data = analytics_service.get_orders_for_export(db)
        
        if not orders_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No orders available for export"
            )
        
        # Export to CSV
        export_path, summary = export_service.export_orders_to_csv(orders_data)
        
        return {
            "status": "success",
            "message": "Orders exported to CSV successfully",
            "export_path": export_path,
            "summary": summary
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/export-info")
def get_export_info():
    """
    Get information about existing CSV exports.
    
    Returns files in export directory with metadata.
    """
    info = export_service.get_export_info()
    return info


# ==================== DUMMY DATA GENERATION ====================

@router.post("/generate-dummy-data")
def generate_dummy_data(
    count: int = Query(default=200, ge=200, le=1000),
    db: Session = Depends(get_db)
):
    """
    Generate and insert realistic dummy orders into database.
    
    Parameters:
        count: Number of dummy orders to generate (200-1000)
    
    Generates diverse scenarios including:
    - Normal orders
    - SLA breaches
    - Different bottleneck patterns
    - Various priority levels
    
    Returns:
    - Total orders generated
    - Insertion statistics
    - SLA breach analysis
    - Bottleneck distribution
    """
    try:
        summary = dummy_data_generator.seed_orders_data(db, count=count)
        
        return {
            "status": "success",
            "message": f"Successfully generated and inserted {summary['total_inserted']} dummy orders",
            "summary": summary
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dummy data generation failed: {str(e)}"
        )


# ==================== ORIGINAL ENDPOINTS (PRESERVED) ====================


@router.get("/priority-breakdown")
def get_priority_breakdown(db: Session = Depends(get_db)):
    """
    Get analytics grouped by order priority.

    Returns avg durations and SLA breach rate per priority (normal, high, urgent).
    Useful for dashboard KPI cards and priority comparison charts.
    """
    try:
        return analytics_service.get_priority_breakdown(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch priority breakdown: {str(e)}"
        )


@router.get("/daily-trend")
def get_daily_order_trend(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get order count and SLA breach count per day for the last N days.

    Returns a time-series list sorted ascending by date.
    Directly consumable by line charts and Tableau date-axis visualizations.
    """
    try:
        return analytics_service.get_daily_order_trend(db, days=days)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch daily trend: {str(e)}"
        )
