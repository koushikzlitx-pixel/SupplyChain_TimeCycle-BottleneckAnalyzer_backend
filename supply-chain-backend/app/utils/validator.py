"""
Validation Utilities

Provides comprehensive validation for supply chain order data.
Handles timestamp validation, lifecycle detection, and data integrity checks.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class OrderValidator:
    """Validator for supply chain order data."""
    
    # Define stage sequence
    LIFECYCLE_STAGES = [
        "order_placed_at",
        "order_confirmed_at",
        "processing_completed_at",
        "shipped_at",
        "delivered_at",
    ]
    
    @staticmethod
    def validate_timestamp_sequence(timestamps: Dict[str, Optional[datetime]]) -> Tuple[bool, List[str]]:
        """
        Validate that timestamps follow logical sequence.
        
        Args:
            timestamps: Dictionary of lifecycle timestamps
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        # Check timestamp types
        for stage, timestamp in timestamps.items():
            if timestamp is not None and not isinstance(timestamp, datetime):
                errors.append(f"{stage} must be a datetime object, got {type(timestamp).__name__}")
        
        if errors:
            return False, errors
        
        # Check sequence - each timestamp should be after previous
        previous_timestamp = None
        previous_stage = None
        
        for stage in OrderValidator.LIFECYCLE_STAGES:
            timestamp = timestamps.get(stage)
            
            if timestamp is None:
                continue
            
            # Check if current timestamp is after previous
            if previous_timestamp is not None:
                if timestamp < previous_timestamp:
                    errors.append(
                        f"{stage} ({timestamp}) is before {previous_stage} ({previous_timestamp})"
                    )
            
            previous_timestamp = timestamp
            previous_stage = stage
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_timestamp_completeness(timestamps: Dict[str, Optional[datetime]]) -> Tuple[bool, Dict[str, bool]]:
        """
        Check which lifecycle stages have timestamps.
        
        Args:
            timestamps: Dictionary of lifecycle timestamps
            
        Returns:
            Tuple of (all_required_present: bool, stage_presence: Dict)
        """
        stage_presence = {}
        
        for stage in OrderValidator.LIFECYCLE_STAGES:
            stage_presence[stage] = timestamps.get(stage) is not None
        
        # All stages complete
        all_present = all(stage_presence.values())
        
        return all_present, stage_presence
    
    @staticmethod
    def validate_durations(
        procurement_time: Optional[float] = None,
        processing_time: Optional[float] = None,
        dispatch_time: Optional[float] = None,
        delivery_time: Optional[float] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate calculated durations.
        
        Args:
            procurement_time: Duration in hours
            processing_time: Duration in hours
            dispatch_time: Duration in hours
            delivery_time: Duration in hours
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        errors = []
        
        durations = {
            "procurement_time": procurement_time,
            "processing_time": processing_time,
            "dispatch_time": dispatch_time,
            "delivery_time": delivery_time,
        }
        
        for stage, duration in durations.items():
            if duration is None:
                continue
            
            # Check type
            if not isinstance(duration, (int, float)):
                errors.append(f"{stage} must be numeric, got {type(duration).__name__}")
            
            # Check negative
            elif duration < 0:
                errors.append(f"{stage} cannot be negative ({duration})")
            
            # Check unreasonably large (more than 180 days)
            elif duration > (180 * 24):
                errors.append(f"{stage} exceeds 180 days ({duration} hours)")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_order_data(order_data: Dict) -> Tuple[bool, List[str], Dict[str, any]]:
        """
        Perform comprehensive validation on order data.
        
        Args:
            order_data: Order dictionary to validate
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str], metadata: Dict)
        """
        errors = []
        metadata = {
            "has_timestamps": False,
            "has_all_timestamps": False,
            "timestamp_errors": [],
            "duration_errors": [],
            "duration_warnings": [],
        }
        
        # Extract timestamps
        timestamps = {
            "order_placed_at": order_data.get("order_placed_at"),
            "order_confirmed_at": order_data.get("order_confirmed_at"),
            "processing_completed_at": order_data.get("processing_completed_at"),
            "shipped_at": order_data.get("shipped_at"),
            "delivered_at": order_data.get("delivered_at"),
        }
        
        # Check if any timestamps present
        has_timestamps = any(v is not None for v in timestamps.values())
        metadata["has_timestamps"] = has_timestamps
        
        if has_timestamps:
            # Validate sequence
            is_valid, sequence_errors = OrderValidator.validate_timestamp_sequence(timestamps)
            if not is_valid:
                errors.extend(sequence_errors)
                metadata["timestamp_errors"] = sequence_errors
            
            # Check completeness
            all_present, stage_presence = OrderValidator.validate_timestamp_completeness(timestamps)
            metadata["has_all_timestamps"] = all_present
            
            # Validate durations if present
            is_valid, duration_errors = OrderValidator.validate_durations(
                order_data.get("procurement_time"),
                order_data.get("processing_time"),
                order_data.get("dispatch_time"),
                order_data.get("delivery_time"),
            )
            
            if not is_valid:
                errors.extend(duration_errors)
                metadata["duration_errors"] = duration_errors
        
        # Validate required fields
        required_fields = ["order_number", "customer_name", "product_name", "quantity"]
        
        for field in required_fields:
            if not order_data.get(field):
                errors.append(f"Required field missing: {field}")
        
        # Validate quantity
        quantity = order_data.get("quantity")
        if quantity is not None:
            if not isinstance(quantity, int) or quantity <= 0:
                errors.append(f"Quantity must be positive integer, got {quantity}")
        
        return len(errors) == 0, errors, metadata


# Singleton instance
order_validator = OrderValidator()
