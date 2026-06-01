"""
Bottleneck Detection Engine

Analyzes stage durations to identify the bottleneck stage with the highest delay.
Safely handles missing values and provides reusable analytics logic.
"""

from typing import Optional, Dict, List, Tuple


def identify_bottleneck(
    procurement_time: Optional[float] = None,
    processing_time: Optional[float] = None,
    dispatch_time_duration: Optional[float] = None,
    delivery_time_duration: Optional[float] = None,
    # Backward-compatible aliases
    dispatch_time: Optional[float] = None,
    delivery_time: Optional[float] = None,
) -> Optional[str]:
    """
    Identify the bottleneck stage with the highest duration.

    Args:
        procurement_time: Duration for procurement stage (hours)
        processing_time: Duration for processing stage (hours)
        dispatch_time_duration: Duration for dispatch stage (hours)
        delivery_time_duration: Duration for delivery stage (hours)

    Returns:
        Name of the bottleneck stage, or None if no valid durations found
    """
    resolved_dispatch = dispatch_time_duration if dispatch_time_duration is not None else dispatch_time
    resolved_delivery = delivery_time_duration if delivery_time_duration is not None else delivery_time

    stages = {
        "procurement": procurement_time,
        "processing": processing_time,
        "dispatch": resolved_dispatch,
        "delivery": resolved_delivery,
    }
    
    # Filter out None values
    valid_stages = {name: duration for name, duration in stages.items() if duration is not None}
    
    if not valid_stages:
        return None
    
    # Find stage with maximum duration
    bottleneck_stage = max(valid_stages, key=valid_stages.get)
    return bottleneck_stage


def analyze_bottlenecks(
    procurement_time: Optional[float] = None,
    processing_time: Optional[float] = None,
    dispatch_time_duration: Optional[float] = None,
    delivery_time_duration: Optional[float] = None,
    # Backward-compatible aliases
    dispatch_time: Optional[float] = None,
    delivery_time: Optional[float] = None,
) -> Dict[str, any]:
    """
    Perform comprehensive bottleneck analysis on all stages.

    Args:
        procurement_time: Duration for procurement stage (hours)
        processing_time: Duration for processing stage (hours)
        dispatch_time_duration: Duration for dispatch stage (hours)
        delivery_time_duration: Duration for delivery stage (hours)

    Returns:
        Dictionary with bottleneck_stage, bottleneck_duration, stage_rankings,
        and stage_percentages
    """
    resolved_dispatch = dispatch_time_duration if dispatch_time_duration is not None else dispatch_time
    resolved_delivery = delivery_time_duration if delivery_time_duration is not None else delivery_time

    stages = {
        "procurement": procurement_time,
        "processing": processing_time,
        "dispatch": resolved_dispatch,
        "delivery": resolved_delivery,
    }
    
    # Filter out None values
    valid_stages = {name: duration for name, duration in stages.items() if duration is not None}
    
    if not valid_stages:
        return {
            "bottleneck_stage": None,
            "bottleneck_duration": None,
            "stage_rankings": [],
            "stage_percentages": {}
        }
    
    # Calculate total time
    total_duration = sum(valid_stages.values())
    
    # Find bottleneck
    bottleneck_stage = max(valid_stages, key=valid_stages.get)
    bottleneck_duration = valid_stages[bottleneck_stage]
    
    # Create rankings
    stage_rankings = sorted(
        valid_stages.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Calculate percentages
    stage_percentages = {}
    if total_duration > 0:
        stage_percentages = {
            name: round((duration / total_duration) * 100, 2)
            for name, duration in valid_stages.items()
        }
    
    return {
        "bottleneck_stage": bottleneck_stage,
        "bottleneck_duration": bottleneck_duration,
        "stage_rankings": stage_rankings,
        "stage_percentages": stage_percentages,
        "total_duration": total_duration
    }


def get_top_bottlenecks(
    orders_data: List[Dict],
    top_n: int = 5
) -> List[Dict]:
    """
    Identify top N orders with the most severe bottlenecks.
    
    Args:
        orders_data: List of order dictionaries with duration fields
        top_n: Number of top bottlenecks to return
        
    Returns:
        List of orders sorted by bottleneck severity
    """
    bottleneck_orders = []
    
    for order in orders_data:
        analysis = analyze_bottlenecks(
            order.get("procurement_time"),
            order.get("processing_time"),
            dispatch_time_duration=order.get("dispatch_time_duration"),
            delivery_time_duration=order.get("delivery_time_duration")
        )
        
        if analysis["bottleneck_stage"]:
            bottleneck_orders.append({
                "order_id": order.get("id"),
                "order_number": order.get("order_number"),
                "bottleneck_stage": analysis["bottleneck_stage"],
                "bottleneck_duration": analysis["bottleneck_duration"],
                "total_duration": analysis["total_duration"]
            })
    
    # Sort by bottleneck duration (descending)
    bottleneck_orders.sort(key=lambda x: x["bottleneck_duration"], reverse=True)
    
    return bottleneck_orders[:top_n]


def compare_stage_performance(
    current_duration: Optional[float],
    average_duration: Optional[float]
) -> Optional[Dict]:
    """
    Compare current stage duration against average.
    
    Args:
        current_duration: Current stage duration (hours)
        average_duration: Average duration for this stage (hours)
        
    Returns:
        Dictionary with comparison metrics or None
    """
    if current_duration is None or average_duration is None or average_duration == 0:
        return None
    
    difference = current_duration - average_duration
    percentage_diff = (difference / average_duration) * 100
    
    return {
        "current": current_duration,
        "average": average_duration,
        "difference": round(difference, 2),
        "percentage_difference": round(percentage_diff, 2),
        "is_above_average": current_duration > average_duration
    }
