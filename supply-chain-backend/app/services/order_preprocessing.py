"""
Order Preprocessing Pipeline

Orchestrates the analytics processing flow for orders:
1. Calculates all stage durations
2. Performs SLA validation
3. Detects bottleneck stages
4. Injects analytics fields into order data

Provides a clean, reusable pipeline for order analytics processing.
"""

from typing import Dict, Optional, Any
from datetime import datetime

from app.utils.time_calculator import calculate_all_durations
from app.utils.sla_detector import check_sla_breach, get_sla_status
from app.utils.bottleneck_detector import identify_bottleneck, analyze_bottlenecks
from app.utils.validator import order_validator


class OrderPreprocessor:
    """
    Preprocessing pipeline for supply chain order analytics.
    
    Transforms raw order lifecycle data into analytics-ready records with:
    - Calculated stage durations
    - SLA breach detection
    - Bottleneck identification
    """
    
    def __init__(self, custom_sla_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize preprocessor with optional custom SLA thresholds.
        
        Args:
            custom_sla_thresholds: Optional custom SLA thresholds to override defaults
        """
        self.custom_sla_thresholds = custom_sla_thresholds
    
    def extract_timestamps(self, order_data: Dict[str, Any]) -> Dict[str, Optional[datetime]]:
        """
        Extract lifecycle timestamps from order data.
        
        Args:
            order_data: Raw order data dictionary
            
        Returns:
            Dictionary of timestamp fields
        """
        return {
            "order_placed_at": order_data.get("order_placed_at"),
            "order_confirmed_at": order_data.get("order_confirmed_at"),
            "processing_completed_at": order_data.get("processing_completed_at"),
            "shipped_at": order_data.get("shipped_at"),
            "delivered_at": order_data.get("delivered_at"),
        }
    
    def validate_timestamps(self, timestamps: Dict[str, Optional[datetime]]) -> Dict[str, Any]:
        """
        Validate timestamp sequences for logical consistency.
        
        Args:
            timestamps: Dictionary of timestamps
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }

        # Centralized sequence/type validation
        is_valid_sequence, sequence_errors = order_validator.validate_timestamp_sequence(timestamps)
        if not is_valid_sequence:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(sequence_errors)

        all_present, stage_presence = order_validator.validate_timestamp_completeness(timestamps)
        validation_result["has_all_timestamps"] = all_present
        validation_result["stage_presence"] = stage_presence
        
        # Check for negative durations (invalid sequences)
        timestamp_order = [
            ("order_placed_at", "order_confirmed_at"),
            ("order_confirmed_at", "processing_completed_at"),
            ("processing_completed_at", "shipped_at"),
            ("shipped_at", "delivered_at"),
        ]
        
        for start_key, end_key in timestamp_order:
            start_time = timestamps.get(start_key)
            end_time = timestamps.get(end_key)
            
            if start_time and end_time:
                if end_time < start_time:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(
                        f"Invalid sequence: {end_key} is before {start_key}"
                    )
        
        return validation_result
    
    def calculate_durations(self, timestamps: Dict[str, Optional[datetime]]) -> Dict[str, Optional[float]]:
        """
        Calculate all stage durations.
        
        Args:
            timestamps: Dictionary of lifecycle timestamps
            
        Returns:
            Dictionary of calculated durations
        """
        return calculate_all_durations(timestamps)
    
    def detect_sla_breach(self, durations: Dict[str, Optional[float]]) -> Dict[str, Any]:
        """
        Detect SLA breaches and identify breached stage.
        
        Args:
            durations: Dictionary of stage durations
            
        Returns:
            Dictionary with SLA breach information
        """
        sla_breach, breached_stage = check_sla_breach(
            procurement_time=durations.get("procurement_time"),
            processing_time=durations.get("processing_time"),
            dispatch_time_duration=durations.get("dispatch_time_duration"),
            delivery_time_duration=durations.get("delivery_time_duration"),
            custom_thresholds=self.custom_sla_thresholds
        )
        
        return {
            "sla_breach": sla_breach,
            "breached_stage": breached_stage
        }
    
    def detect_bottleneck(self, durations: Dict[str, Optional[float]]) -> Optional[str]:
        """
        Identify bottleneck stage.
        
        Args:
            durations: Dictionary of stage durations
            
        Returns:
            Name of bottleneck stage or None
        """
        return identify_bottleneck(
            procurement_time=durations.get("procurement_time"),
            processing_time=durations.get("processing_time"),
            dispatch_time_duration=durations.get("dispatch_time_duration"),
            delivery_time_duration=durations.get("delivery_time_duration")
        )
    
    def process_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete preprocessing pipeline on order data.
        
        Pipeline steps:
        1. Extract timestamps
        2. Validate timestamp sequences
        3. Calculate stage durations
        4. Detect SLA breaches
        5. Identify bottleneck stage
        6. Inject analytics fields
        
        Args:
            order_data: Raw order data dictionary
            
        Returns:
            Order data enriched with analytics fields
        """
        # Step 1: Extract timestamps
        timestamps = self.extract_timestamps(order_data)
        
        # Step 2: Validate timestamps
        validation = self.validate_timestamps(timestamps)

        if not validation.get("is_valid"):
            return {
                **order_data,
                "procurement_time": None,
                "processing_time": None,
                "dispatch_time_duration": None,
                "delivery_time_duration": None,
                "total_time": None,
                "sla_breach": False,
                "breached_stage": None,
                "bottleneck_stage": None,
                "validation_errors": validation.get("errors", []),
            }
        
        # Step 3: Calculate durations
        durations = self.calculate_durations(timestamps)

        durations_valid, duration_errors = order_validator.validate_durations(
            procurement_time=durations.get("procurement_time"),
            processing_time=durations.get("processing_time"),
            dispatch_time_duration=durations.get("dispatch_time_duration"),
            delivery_time_duration=durations.get("delivery_time_duration"),
        )

        if not durations_valid:
            validation["errors"].extend(duration_errors)
        
        # Step 4: Detect SLA breaches
        sla_info = self.detect_sla_breach(durations)
        
        # Step 5: Identify bottleneck
        bottleneck_stage = self.detect_bottleneck(durations)
        
        # Step 6: Inject analytics fields into order data
        analytics_fields = {
            # Duration fields
            "procurement_time": durations.get("procurement_time"),
            "processing_time": durations.get("processing_time"),
            "dispatch_time_duration": durations.get("dispatch_time_duration"),
            "delivery_time_duration": durations.get("delivery_time_duration"),
            "total_time": durations.get("total_time"),
            
            # SLA fields
            "sla_breach": sla_info["sla_breach"],
            "breached_stage": sla_info["breached_stage"],
            
            # Bottleneck field
            "bottleneck_stage": bottleneck_stage,
            
            # Validation
            "validation_errors": validation.get("errors"),
        }
        
        # Merge analytics fields with original order data
        processed_order = {**order_data, **analytics_fields}
        
        return processed_order
    
    def get_detailed_analysis(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive analytics report for an order.
        
        Args:
            order_data: Order data with lifecycle timestamps
            
        Returns:
            Detailed analytics report
        """
        timestamps = self.extract_timestamps(order_data)
        durations = self.calculate_durations(timestamps)
        
        # Get detailed SLA status
        sla_status = get_sla_status(
            procurement_time=durations.get("procurement_time"),
            processing_time=durations.get("processing_time"),
            dispatch_time_duration=durations.get("dispatch_time_duration"),
            delivery_time_duration=durations.get("delivery_time_duration"),
            custom_thresholds=self.custom_sla_thresholds
        )
        
        # Get detailed bottleneck analysis
        bottleneck_analysis = analyze_bottlenecks(
            procurement_time=durations.get("procurement_time"),
            processing_time=durations.get("processing_time"),
            dispatch_time_duration=durations.get("dispatch_time_duration"),
            delivery_time_duration=durations.get("delivery_time_duration")
        )
        
        return {
            "order_id": order_data.get("id"),
            "order_number": order_data.get("order_number"),
            "durations": durations,
            "sla_status": sla_status,
            "bottleneck_analysis": bottleneck_analysis,
            "timestamps": timestamps
        }


# Singleton instance for easy import
default_preprocessor = OrderPreprocessor()
