"""
SLA Detection Engine

Provides configurable SLA validation logic for supply chain stages.
Detects SLA breaches and identifies which stage violated the threshold.
"""

from typing import Optional, Tuple, Dict


# Configurable SLA Thresholds (in hours)
SLA_THRESHOLDS = {
    "procurement": 24.0,      # 1 day for order confirmation
    "processing": 72.0,       # 3 days for processing
    "dispatch": 12.0,         # 12 hours for dispatch
    "delivery": 48.0,         # 2 days for delivery
}


def check_sla_breach(
    procurement_time: Optional[float] = None,
    processing_time: Optional[float] = None,
    dispatch_time: Optional[float] = None,
    delivery_time: Optional[float] = None,
    custom_thresholds: Optional[Dict[str, float]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check if any stage has breached its SLA threshold.
    
    Args:
        procurement_time: Duration for procurement stage (hours)
        processing_time: Duration for processing stage (hours)
        dispatch_time: Duration for dispatch stage (hours)
        delivery_time: Duration for delivery stage (hours)
        custom_thresholds: Optional custom SLA thresholds to override defaults
        
    Returns:
        Tuple of (sla_breach: bool, breached_stage: str or None)
        - sla_breach: True if any stage breached SLA
        - breached_stage: Name of the first stage that breached SLA, or None
    """
    thresholds = custom_thresholds if custom_thresholds else SLA_THRESHOLDS
    
    # Check each stage in order
    stages_to_check = [
        ("procurement", procurement_time, thresholds.get("procurement")),
        ("processing", processing_time, thresholds.get("processing")),
        ("dispatch", dispatch_time, thresholds.get("dispatch")),
        ("delivery", delivery_time, thresholds.get("delivery")),
    ]
    
    for stage_name, duration, threshold in stages_to_check:
        # Skip if duration or threshold is not available
        if duration is None or threshold is None:
            continue
            
        # Check if duration exceeds threshold
        if duration > threshold:
            return True, stage_name
    
    # No breach detected
    return False, None


def get_sla_status(
    procurement_time: Optional[float] = None,
    processing_time: Optional[float] = None,
    dispatch_time: Optional[float] = None,
    delivery_time: Optional[float] = None,
    custom_thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, any]:
    """
    Get detailed SLA status for all stages.
    
    Args:
        procurement_time: Duration for procurement stage (hours)
        processing_time: Duration for processing stage (hours)
        dispatch_time: Duration for dispatch stage (hours)
        delivery_time: Duration for delivery stage (hours)
        custom_thresholds: Optional custom SLA thresholds
        
    Returns:
        Dictionary containing:
            - sla_breach: Overall breach status
            - breached_stage: First stage that breached (or None)
            - stage_details: Per-stage breach information
    """
    sla_breach, breached_stage = check_sla_breach(
        procurement_time, processing_time, dispatch_time, delivery_time, custom_thresholds
    )
    
    thresholds = custom_thresholds if custom_thresholds else SLA_THRESHOLDS
    
    # Build detailed stage information
    stage_details = {}
    stages = {
        "procurement": procurement_time,
        "processing": processing_time,
        "dispatch": dispatch_time,
        "delivery": delivery_time,
    }
    
    for stage_name, duration in stages.items():
        threshold = thresholds.get(stage_name)
        if duration is not None and threshold is not None:
            stage_details[stage_name] = {
                "duration": duration,
                "threshold": threshold,
                "breached": duration > threshold,
                "margin": duration - threshold
            }
    
    return {
        "sla_breach": sla_breach,
        "breached_stage": breached_stage,
        "stage_details": stage_details
    }


def update_sla_threshold(stage: str, threshold_hours: float) -> bool:
    """
    Update SLA threshold for a specific stage.
    
    Args:
        stage: Stage name (procurement, processing, dispatch, delivery)
        threshold_hours: New threshold in hours
        
    Returns:
        True if updated successfully, False if stage not found
    """
    if stage in SLA_THRESHOLDS:
        SLA_THRESHOLDS[stage] = threshold_hours
        return True
    return False


def get_sla_thresholds() -> Dict[str, float]:
    """
    Get current SLA thresholds for all stages.
    
    Returns:
        Dictionary of stage names to threshold hours
    """
    return SLA_THRESHOLDS.copy()
