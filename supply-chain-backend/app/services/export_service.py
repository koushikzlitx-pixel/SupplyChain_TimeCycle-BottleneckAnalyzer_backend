"""
CSV Export Service

Provides CSV export functionality for orders with analytics data.
Converts orders to pandas DataFrame and exports to CSV format.
Suitable for Tableau and other BI tools.
"""

import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path

from app.services.analytics_service import AnalyticsService


class ExportService:
    """Service for exporting analytics data to CSV format."""
    
    # Default export directory
    EXPORT_DIR = "data/processed"
    EXPORT_FILENAME = "orders_export.csv"
    
    @staticmethod
    def _ensure_export_directory() -> None:
        """
        Create export directory if it doesn't exist.
        """
        Path(ExportService.EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _validate_orders_data(orders_data: List[Dict[str, Any]]) -> None:
        """Validate export payload before DataFrame conversion."""
        if not isinstance(orders_data, list) or len(orders_data) == 0:
            raise ValueError("No processed orders available for export")

        if not all(isinstance(item, dict) for item in orders_data):
            raise ValueError("Invalid export payload: each row must be a dictionary")

        required_columns = [
            "order_placed_at",
            "order_confirmed_at",
            "processing_completed_at",
            "shipped_at",
            "delivered_at",
            "procurement_time",
            "processing_time",
            "dispatch_time_duration",
            "delivery_time_duration",
            "total_time",
            "sla_breach",
            "breached_stage",
            "bottleneck_stage",
        ]

        first_row = orders_data[0]
        missing_columns = [col for col in required_columns if col not in first_row]
        if missing_columns:
            raise ValueError(
                f"Export payload missing required analytics columns: {', '.join(missing_columns)}"
            )

    @staticmethod
    def export_orders_to_csv(orders_data: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """
        Export orders to CSV file.
        
        Args:
            orders_data: List of order dictionaries from analytics service
            
        Returns:
            Tuple of (export_path, summary_dict)
        """
        ExportService._validate_orders_data(orders_data)

        # Ensure directory exists
        ExportService._ensure_export_directory()
        
        # Convert to DataFrame
        df = pd.DataFrame(orders_data)
        
        # Prepare columns in logical order
        column_order = [
            # Identifiers
            "order_id",
            "order_number",
            "customer_name",
            "customer_email",
            "product_name",
            "quantity",
            "priority",
            "status",
            
            # Lifecycle Timestamps
            "order_placed_at",
            "order_confirmed_at",
            "processing_completed_at",
            "shipped_at",
            "delivered_at",
            
            # Stage Durations (Hours)
            "procurement_time",
            "processing_time",
            "dispatch_time_duration",
            "delivery_time_duration",
            "total_time",
            
            # SLA Analysis
            "sla_breach",
            "breached_stage",
            
            # Bottleneck Analysis
            "bottleneck_stage",
            
            # Metadata
            "created_at",
            "updated_at",
        ]
        
        # Reorder columns (only include available columns)
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]
        
        # Format datetime columns
        datetime_columns = [
            "order_placed_at",
            "order_confirmed_at",
            "processing_completed_at",
            "shipped_at",
            "delivered_at",
            "created_at",
            "updated_at"
        ]
        
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Format numeric columns to 2 decimals
        numeric_columns = [
            "procurement_time",
            "processing_time",
            "dispatch_time_duration",
            "delivery_time_duration",
            "total_time"
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

        if "sla_breach" in df.columns:
            df["sla_breach"] = df["sla_breach"].fillna(False).astype(bool)

        for col in ["breached_stage", "bottleneck_stage", "priority", "status"]:
            if col in df.columns:
                df[col] = df[col].fillna("N/A")
        
        # Create export path with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = os.path.join(
            ExportService.EXPORT_DIR,
            f"orders_export_{timestamp}.csv"
        )
        
        # Also save to standard location
        standard_path = os.path.join(
            ExportService.EXPORT_DIR,
            ExportService.EXPORT_FILENAME
        )
        
        # Export to CSV
        df.to_csv(export_path, index=False)
        df.to_csv(standard_path, index=False)
        
        # Create summary
        summary = {
            "export_timestamp": datetime.now().isoformat(),
            "total_records": len(df),
            "columns": len(df.columns),
            "file_path": export_path,
            "standard_path": standard_path,
            "file_size_kb": round(os.path.getsize(export_path) / 1024, 2),
            "stats": {
                "total_orders": len(df),
                "sla_breaches": int(df["sla_breach"].sum()) if "sla_breach" in df.columns else 0,
                "orders_by_priority": df["priority"].value_counts().to_dict() if "priority" in df.columns else {},
                "orders_by_status": df["status"].value_counts().to_dict() if "status" in df.columns else {},
                "bottleneck_distribution": df["bottleneck_stage"].value_counts().to_dict() if "bottleneck_stage" in df.columns else {},
            }
        }
        
        return export_path, summary
    
    @staticmethod
    def export_analytics_summary_to_csv(
        analytics_data: Dict[str, Any],
        filename: str = "analytics_summary.csv"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Export analytics summary as CSV.
        
        Args:
            analytics_data: Analytics summary dictionary
            filename: Output filename
            
        Returns:
            Tuple of (export_path, summary_dict)
        """
        # Ensure directory exists
        ExportService._ensure_export_directory()
        
        # Flatten analytics data for CSV
        flattened_data = []
        
        for key, value in analytics_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flattened_data.append({
                        "metric": key,
                        "category": sub_key,
                        "value": sub_value
                    })
            else:
                flattened_data.append({
                    "metric": key,
                    "category": "-",
                    "value": value
                })
        
        df = pd.DataFrame(flattened_data)
        
        # Create export path
        export_path = os.path.join(ExportService.EXPORT_DIR, filename)
        
        # Export
        df.to_csv(export_path, index=False)
        
        summary = {
            "export_timestamp": datetime.now().isoformat(),
            "file_path": export_path,
            "file_size_kb": round(os.path.getsize(export_path) / 1024, 2),
            "total_metrics": len(flattened_data),
        }
        
        return export_path, summary
    
    @staticmethod
    def get_export_info() -> Dict[str, Any]:
        """
        Get information about existing exports.
        
        Returns:
            Dictionary with export directory info
        """
        info = {
            "export_directory": ExportService.EXPORT_DIR,
            "directory_exists": os.path.exists(ExportService.EXPORT_DIR),
            "files": [],
        }
        
        if info["directory_exists"]:
            try:
                for file in os.listdir(ExportService.EXPORT_DIR):
                    file_path = os.path.join(ExportService.EXPORT_DIR, file)
                    if os.path.isfile(file_path):
                        info["files"].append({
                            "filename": file,
                            "path": file_path,
                            "size_kb": round(os.path.getsize(file_path) / 1024, 2),
                            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                        })
            except Exception as e:
                info["error"] = str(e)
        
        return info


# Singleton instance
export_service = ExportService()
