"""
Time Calculation Engine

Provides reusable utilities for calculating stage durations in the supply chain lifecycle.
Handles null timestamps, prevents negative durations, and ensures proper rounding.
"""

from datetime import datetime
from typing import Optional


def calculate_duration(start_time: Optional[datetime], end_time: Optional[datetime]) -> Optional[float]:
    """
    Calculate duration in hours between two timestamps.
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp
        
    Returns:
        Duration in hours (rounded to 2 decimals), or None if either timestamp is missing
        Returns None for negative durations (invalid sequences)
    """
    if start_time is None or end_time is None:
        return None
    
    duration_seconds = (end_time - start_time).total_seconds()
    
    # Prevent negative durations
    if duration_seconds < 0:
        return None
    
    # Convert to hours and round to 2 decimal places
    duration_hours = duration_seconds / 3600
    return round(duration_hours, 2)


def calculate_procurement_time(
    order_placed_at: Optional[datetime],
    order_confirmed_at: Optional[datetime]
) -> Optional[float]:
    """
    Calculate procurement time (order placed to order confirmed).
    
    Args:
        order_placed_at: When order was placed
        order_confirmed_at: When order was confirmed
        
    Returns:
        Procurement duration in hours
    """
    return calculate_duration(order_placed_at, order_confirmed_at)


def calculate_processing_time(
    order_confirmed_at: Optional[datetime],
    processing_completed_at: Optional[datetime]
) -> Optional[float]:
    """
    Calculate processing time (order confirmed to processing completed).
    
    Args:
        order_confirmed_at: When order was confirmed
        processing_completed_at: When processing was completed
        
    Returns:
        Processing duration in hours
    """
    return calculate_duration(order_confirmed_at, processing_completed_at)


def calculate_dispatch_time_duration(
    processing_completed_at: Optional[datetime],
    shipped_at: Optional[datetime]
) -> Optional[float]:
    """
    Calculate dispatch time duration (processing completed to shipped).

    Args:
        processing_completed_at: When processing was completed
        shipped_at: When order was shipped

    Returns:
        Dispatch duration in hours
    """
    return calculate_duration(processing_completed_at, shipped_at)


# Backward-compatible alias
calculate_dispatch_time = calculate_dispatch_time_duration


def calculate_delivery_time_duration(
    shipped_at: Optional[datetime],
    delivered_at: Optional[datetime]
) -> Optional[float]:
    """
    Calculate delivery time duration (shipped to delivered).

    Args:
        shipped_at: When order was shipped
        delivered_at: When order was delivered

    Returns:
        Delivery duration in hours
    """
    return calculate_duration(shipped_at, delivered_at)


# Backward-compatible alias
calculate_delivery_time = calculate_delivery_time_duration


def calculate_total_time(
    order_placed_at: Optional[datetime],
    delivered_at: Optional[datetime]
) -> Optional[float]:
    """
    Calculate total lifecycle time (order placed to delivered).
    
    Args:
        order_placed_at: When order was placed
        delivered_at: When order was delivered
        
    Returns:
        Total duration in hours
    """
    return calculate_duration(order_placed_at, delivered_at)


def calculate_all_durations(timestamps: dict) -> dict:
    """
    Calculate all stage durations from a dictionary of timestamps.
    
    Args:
        timestamps: Dictionary containing all lifecycle timestamps:
            - order_placed_at
            - order_confirmed_at
            - processing_completed_at
            - shipped_at
            - delivered_at
            
    Returns:
        Dictionary with calculated durations:
            - procurement_time
            - processing_time
            - dispatch_time_duration
            - delivery_time_duration
            - total_time
    """
    return {
        "procurement_time": calculate_procurement_time(
            timestamps.get("order_placed_at"),
            timestamps.get("order_confirmed_at")
        ),
        "processing_time": calculate_processing_time(
            timestamps.get("order_confirmed_at"),
            timestamps.get("processing_completed_at")
        ),
        "dispatch_time_duration": calculate_dispatch_time_duration(
            timestamps.get("processing_completed_at"),
            timestamps.get("shipped_at")
        ),
        "delivery_time_duration": calculate_delivery_time_duration(
            timestamps.get("shipped_at"),
            timestamps.get("delivered_at")
        ),
        "total_time": calculate_total_time(
            timestamps.get("order_placed_at"),
            timestamps.get("delivered_at")
        ),
    }
