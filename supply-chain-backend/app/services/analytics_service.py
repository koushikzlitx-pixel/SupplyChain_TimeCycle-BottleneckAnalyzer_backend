"""
Analytics Service

Provides reusable analytics aggregation and reporting functions.
Handles complex queries with efficient SQLAlchemy patterns for:
- Summary analytics
- Bottleneck analysis
- SLA breach reporting
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.models import Order, OrderStatus as ModelOrderStatus


class AnalyticsService:
    """Service for analytics aggregation and reporting."""
    
    @staticmethod
    def get_summary_analytics(db: Session) -> Dict[str, Any]:
        """
        Get comprehensive summary analytics across all orders.
        
        Returns:
            Dictionary with:
            - total_orders
            - completed_orders
            - pending_orders
            - average_total_time
            - average_procurement_time
            - average_processing_time
            - average_dispatch_time
            - average_delivery_time
            - sla_breach_count
            - sla_breach_percentage
            - bottleneck_distribution
        """
        # Total orders count
        total_orders = db.query(func.count(Order.id)).scalar() or 0
        
        # Orders by status
        completed_orders = db.query(func.count(Order.id)).filter(
            Order.status == ModelOrderStatus.COMPLETED
        ).scalar() or 0
        
        pending_orders = db.query(func.count(Order.id)).filter(
            Order.status == ModelOrderStatus.PENDING
        ).scalar() or 0
        
        # Average times (only for completed orders with data)
        avg_total = db.query(func.avg(Order.total_time)).filter(
            Order.total_time.isnot(None)
        ).scalar()
        
        avg_procurement = db.query(func.avg(Order.procurement_time)).filter(
            Order.procurement_time.isnot(None)
        ).scalar()
        
        avg_processing = db.query(func.avg(Order.processing_time)).filter(
            Order.processing_time.isnot(None)
        ).scalar()
        
        avg_dispatch = db.query(func.avg(Order.dispatch_time)).filter(
            Order.dispatch_time.isnot(None)
        ).scalar()
        
        avg_delivery = db.query(func.avg(Order.delivery_time)).filter(
            Order.delivery_time.isnot(None)
        ).scalar()
        
        # SLA breach analysis
        sla_breaches = db.query(func.count(Order.id)).filter(
            Order.sla_breach == True
        ).scalar() or 0
        
        sla_breach_percentage = round(
            (sla_breaches / total_orders * 100), 2
        ) if total_orders > 0 else 0
        
        # Bottleneck distribution
        bottleneck_data = db.query(
            Order.bottleneck_stage,
            func.count(Order.id).label('count')
        ).filter(
            Order.bottleneck_stage.isnot(None)
        ).group_by(Order.bottleneck_stage).all()
        
        bottleneck_distribution = {stage: count for stage, count in bottleneck_data}
        
        return {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "pending_orders": pending_orders,
            "average_durations": {
                "total_time": round(avg_total, 2) if avg_total else None,
                "procurement_time": round(avg_procurement, 2) if avg_procurement else None,
                "processing_time": round(avg_processing, 2) if avg_processing else None,
                "dispatch_time": round(avg_dispatch, 2) if avg_dispatch else None,
                "delivery_time": round(avg_delivery, 2) if avg_delivery else None,
            },
            "sla_analysis": {
                "total_breaches": sla_breaches,
                "breach_percentage": sla_breach_percentage,
            },
            "bottleneck_distribution": bottleneck_distribution,
        }
    
    @staticmethod
    def get_bottleneck_analytics(db: Session, limit: int = 100) -> Dict[str, Any]:
        """
        Get detailed bottleneck analysis.
        
        Returns:
            Dictionary with:
            - total_with_bottleneck
            - bottleneck_stages (with counts and percentages)
            - top_bottleneck_orders (slowest orders by bottleneck)
        """
        # Get all orders with bottleneck
        bottleneck_query = db.query(Order).filter(
            Order.bottleneck_stage.isnot(None)
        ).all()
        
        total_with_bottleneck = len(bottleneck_query)
        
        # Bottleneck distribution
        bottleneck_counts = db.query(
            Order.bottleneck_stage,
            func.count(Order.id).label('count')
        ).filter(
            Order.bottleneck_stage.isnot(None)
        ).group_by(Order.bottleneck_stage).all()
        
        bottleneck_stages = []
        for stage, count in bottleneck_counts:
            percentage = round(
                (count / total_with_bottleneck * 100), 2
            ) if total_with_bottleneck > 0 else 0
            
            bottleneck_stages.append({
                "stage": stage,
                "count": count,
                "percentage": percentage,
            })
        
        # Top bottleneck orders (slowest)
        top_bottleneck_orders = db.query(
            Order.id,
            Order.order_number,
            Order.bottleneck_stage,
            Order.total_time,
        ).filter(
            Order.bottleneck_stage.isnot(None)
        ).order_by(Order.total_time.desc()).limit(limit).all()
        
        top_orders_list = [
            {
                "order_id": order.id,
                "order_number": order.order_number,
                "bottleneck_stage": order.bottleneck_stage,
                "total_time": order.total_time,
            }
            for order in top_bottleneck_orders
        ]
        
        return {
            "total_with_bottleneck": total_with_bottleneck,
            "bottleneck_stages": bottleneck_stages,
            "top_bottleneck_orders": top_orders_list,
        }
    
    @staticmethod
    def get_sla_breach_analytics(db: Session, limit: int = 100) -> Dict[str, Any]:
        """
        Get detailed SLA breach analysis.
        
        Returns:
            Dictionary with:
            - total_breaches
            - breach_percentage
            - breached_stages (with counts)
            - breached_orders (with stage and time)
        """
        # Total SLA breaches
        breach_query = db.query(Order).filter(Order.sla_breach == True).all()
        total_breaches = len(breach_query)
        
        # Total orders for percentage calculation
        total_orders = db.query(func.count(Order.id)).scalar() or 0
        
        breach_percentage = round(
            (total_breaches / total_orders * 100), 2
        ) if total_orders > 0 else 0
        
        # Breached stages distribution
        breached_stage_data = db.query(
            Order.breached_stage,
            func.count(Order.id).label('count')
        ).filter(
            Order.sla_breach == True,
            Order.breached_stage.isnot(None)
        ).group_by(Order.breached_stage).all()
        
        breached_stages = {stage: count for stage, count in breached_stage_data}
        
        # Detailed breached orders
        breached_orders_query = db.query(
            Order.id,
            Order.order_number,
            Order.breached_stage,
            Order.total_time,
            Order.procurement_time,
            Order.processing_time,
            Order.dispatch_time,
            Order.delivery_time,
        ).filter(
            Order.sla_breach == True
        ).order_by(Order.total_time.desc()).limit(limit).all()
        
        breached_orders = [
            {
                "order_id": order.id,
                "order_number": order.order_number,
                "breached_stage": order.breached_stage,
                "total_time": order.total_time,
                "stage_durations": {
                    "procurement_time": order.procurement_time,
                    "processing_time": order.processing_time,
                    "dispatch_time": order.dispatch_time,
                    "delivery_time": order.delivery_time,
                }
            }
            for order in breached_orders_query
        ]
        
        return {
            "total_breaches": total_breaches,
            "breach_percentage": breach_percentage,
            "breached_stages": breached_stages,
            "breached_orders": breached_orders,
        }
    
    @staticmethod
    def get_orders_for_export(db: Session) -> List[Dict[str, Any]]:
        """
        Fetch all orders with analytics fields for export.
        
        Returns:
            List of order dictionaries with all analytics fields
        """
        orders = db.query(Order).filter(
            Order.total_time.isnot(None)
        ).order_by(Order.created_at.desc()).all()
        
        orders_list = []
        for order in orders:
            orders_list.append({
                "order_id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "product_name": order.product_name,
                "quantity": order.quantity,
                "priority": order.priority,
                "status": order.status.value if order.status else None,
                
                # Lifecycle timestamps
                "order_placed_at": order.order_placed_at,
                "order_confirmed_at": order.order_confirmed_at,
                "processing_completed_at": order.processing_completed_at,
                "shipped_at": order.shipped_at,
                "delivered_at": order.delivered_at,
                
                # Durations (hours)
                "procurement_time": order.procurement_time,
                "processing_time": order.processing_time,
                "dispatch_time": order.dispatch_time,
                "delivery_time": order.delivery_time,
                "total_time": order.total_time,
                
                # SLA Analysis
                "sla_breach": order.sla_breach,
                "breached_stage": order.breached_stage,
                
                # Bottleneck Analysis
                "bottleneck_stage": order.bottleneck_stage,
                
                # Metadata
                "created_at": order.created_at,
                "updated_at": order.updated_at,
            })
        
        return orders_list
    
    @staticmethod
    def get_stage_performance_metrics(db: Session) -> Dict[str, Any]:
        """
        Get detailed performance metrics for each stage.
        
        Returns:
            Dictionary with min, max, avg for each stage
        """
        stages = {
            "procurement": Order.procurement_time,
            "processing": Order.processing_time,
            "dispatch": Order.dispatch_time,
            "delivery": Order.delivery_time,
            "total": Order.total_time,
        }
        
        metrics = {}
        
        for stage_name, stage_column in stages.items():
            stats = db.query(
                func.count(stage_column).label('count'),
                func.avg(stage_column).label('average'),
                func.min(stage_column).label('minimum'),
                func.max(stage_column).label('maximum'),
                func.stddev(stage_column).label('stddev'),
            ).filter(stage_column.isnot(None)).first()
            
            if stats and stats.count > 0:
                metrics[stage_name] = {
                    "count": stats.count,
                    "average": round(stats.average, 2) if stats.average else None,
                    "minimum": round(stats.minimum, 2) if stats.minimum else None,
                    "maximum": round(stats.maximum, 2) if stats.maximum else None,
                    "stddev": round(stats.stddev, 2) if stats.stddev else None,
                }
            else:
                metrics[stage_name] = {
                    "count": 0,
                    "average": None,
                    "minimum": None,
                    "maximum": None,
                    "stddev": None,
                }
        
        return metrics


# Singleton instance
analytics_service = AnalyticsService()
