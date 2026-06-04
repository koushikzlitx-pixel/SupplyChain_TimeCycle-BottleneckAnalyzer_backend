"""
Order Service Layer

Provides business logic for order management with integrated analytics preprocessing.
Ensures all orders are processed through the analytics pipeline before persistence.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime

from app.models import Order, OrderStatus as ModelOrderStatus, StageLog
from app.services.order_preprocessing import OrderPreprocessor, default_preprocessor


class OrderService:
    """
    Service layer for order operations with analytics integration.
    
    Handles:
    - Order CRUD operations
    - Analytics preprocessing
    - Aggregation queries
    - Business logic validation
    """
    
    def __init__(self, preprocessor: OrderPreprocessor = None):
        """
        Initialize order service with optional custom preprocessor.
        
        Args:
            preprocessor: OrderPreprocessor instance (uses default if None)
        """
        self.preprocessor = preprocessor or default_preprocessor
    
    def create_order(self, db: Session, order_data: Dict[str, Any]) -> Order:
        """
        Create a new order with analytics preprocessing.
        
        Args:
            db: Database session
            order_data: Order creation data including lifecycle timestamps
            
        Returns:
            Created Order instance with analytics fields
        """
        # Run preprocessing pipeline
        processed_data = self.preprocessor.process_order(order_data)
        
        # Create order instance
        db_order = Order(
            order_number=processed_data.get("order_number"),
            customer_name=processed_data.get("customer_name"),
            customer_email=processed_data.get("customer_email"),
            product_name=processed_data.get("product_name"),
            quantity=processed_data.get("quantity"),
            priority=processed_data.get("priority", "normal"),
            status=processed_data.get("status", ModelOrderStatus.PENDING),
            
            # Lifecycle timestamps
            order_placed_at=processed_data.get("order_placed_at"),
            order_confirmed_at=processed_data.get("order_confirmed_at"),
            processing_completed_at=processed_data.get("processing_completed_at"),
            shipped_at=processed_data.get("shipped_at"),
            delivered_at=processed_data.get("delivered_at"),
            
            # Analytics fields
            procurement_time=processed_data.get("procurement_time"),
            processing_time=processed_data.get("processing_time"),
            dispatch_time_duration=processed_data.get("dispatch_time_duration"),
            delivery_time_duration=processed_data.get("delivery_time_duration"),
            total_time=processed_data.get("total_time"),
            sla_breach=processed_data.get("sla_breach", False),
            breached_stage=processed_data.get("breached_stage"),
            bottleneck_stage=processed_data.get("bottleneck_stage"),
        )
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        return db_order
    
    def update_order(
        self, 
        db: Session, 
        order_id: int, 
        update_data: Dict[str, Any],
        reprocess_analytics: bool = True
    ) -> Optional[Order]:
        """
        Update an existing order with optional analytics reprocessing.
        
        Args:
            db: Database session
            order_id: Order ID to update
            update_data: Fields to update
            reprocess_analytics: Whether to recalculate analytics
            
        Returns:
            Updated Order instance or None if not found
        """
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None
        
        # If reprocessing analytics, prepare full order data
        if reprocess_analytics:
            # Merge existing order data with updates
            order_data = self._order_to_dict(db_order)
            order_data.update(update_data)
            
            # Run preprocessing
            processed_data = self.preprocessor.process_order(order_data)
            
            # Update all fields including analytics
            for field, value in processed_data.items():
                if hasattr(db_order, field):
                    setattr(db_order, field, value)
        else:
            # Update only provided fields
            for field, value in update_data.items():
                if hasattr(db_order, field):
                    setattr(db_order, field, value)
        
        db.commit()
        db.refresh(db_order)
        
        return db_order
    
    def get_order(self, db: Session, order_id: int) -> Optional[Order]:
        """
        Get order by ID.
        
        Args:
            db: Database session
            order_id: Order ID
            
        Returns:
            Order instance or None
        """
        return db.query(Order).filter(Order.id == order_id).first()
    
    def list_orders(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ModelOrderStatus] = None,
        sla_breach: Optional[bool] = None,
        bottleneck_stage: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[Order]:
        """
        List orders with optional filtering.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            status: Filter by order status
            sla_breach: Filter by SLA breach status
            bottleneck_stage: Filter by bottleneck stage
            from_date: Filter orders placed on or after this date
            to_date: Filter orders placed on or before this date
            
        Returns:
            List of Order instances
        """
        query = db.query(Order)
        
        if status:
            query = query.filter(Order.status == status)
        if sla_breach is not None:
            query = query.filter(Order.sla_breach == sla_breach)
        if bottleneck_stage:
            query = query.filter(Order.bottleneck_stage == bottleneck_stage)
        if from_date is not None:
            query = query.filter(Order.order_placed_at >= from_date)
        if to_date is not None:
            query = query.filter(Order.order_placed_at <= to_date)
        
        return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    def delete_order(self, db: Session, order_id: int) -> bool:
        """
        Delete an order.
        
        Args:
            db: Database session
            order_id: Order ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return False
        
        db.delete(db_order)
        db.commit()
        return True
    
    def get_analytics_summary(self, db: Session) -> Dict[str, Any]:
        """
        Get aggregate analytics summary across all orders.
        
        Returns:
            Dictionary with aggregated analytics metrics
        """
        # Total orders
        total_orders = db.query(func.count(Order.id)).scalar()
        
        # SLA breaches
        sla_breaches = db.query(func.count(Order.id)).filter(Order.sla_breach == True).scalar()
        
        # Average durations
        avg_procurement = db.query(func.avg(Order.procurement_time)).filter(
            Order.procurement_time.isnot(None)
        ).scalar()
        avg_processing = db.query(func.avg(Order.processing_time)).filter(
            Order.processing_time.isnot(None)
        ).scalar()
        avg_dispatch = db.query(func.avg(Order.dispatch_time_duration)).filter(
            Order.dispatch_time_duration.isnot(None)
        ).scalar()
        avg_delivery = db.query(func.avg(Order.delivery_time_duration)).filter(
            Order.delivery_time_duration.isnot(None)
        ).scalar()
        avg_total = db.query(func.avg(Order.total_time)).filter(
            Order.total_time.isnot(None)
        ).scalar()
        
        # Bottleneck distribution
        bottleneck_counts = db.query(
            Order.bottleneck_stage,
            func.count(Order.id).label('count')
        ).filter(
            Order.bottleneck_stage.isnot(None)
        ).group_by(Order.bottleneck_stage).all()
        
        return {
            "total_orders": total_orders,
            "sla_breaches": sla_breaches,
            "sla_breach_rate": round((sla_breaches / total_orders * 100), 2) if total_orders > 0 else 0,
            "average_durations": {
                "procurement": round(avg_procurement, 2) if avg_procurement else None,
                "processing": round(avg_processing, 2) if avg_processing else None,
                "dispatch": round(avg_dispatch, 2) if avg_dispatch else None,
                "delivery": round(avg_delivery, 2) if avg_delivery else None,
                "total": round(avg_total, 2) if avg_total else None,
            },
            "bottleneck_distribution": {
                stage: count for stage, count in bottleneck_counts
            }
        }
    
    def get_orders_with_sla_breach(self, db: Session, limit: int = 100) -> List[Order]:
        """
        Get orders that breached SLA.
        
        Args:
            db: Database session
            limit: Maximum number of records
            
        Returns:
            List of orders with SLA breaches
        """
        return db.query(Order).filter(
            Order.sla_breach == True
        ).order_by(Order.created_at.desc()).limit(limit).all()
    
    def get_orders_by_bottleneck(self, db: Session, stage: str, limit: int = 100) -> List[Order]:
        """
        Get orders with specific bottleneck stage.
        
        Args:
            db: Database session
            stage: Bottleneck stage name
            limit: Maximum number of records
            
        Returns:
            List of orders with specified bottleneck
        """
        return db.query(Order).filter(
            Order.bottleneck_stage == stage
        ).order_by(Order.total_time.desc()).limit(limit).all()
    
    def _order_to_dict(self, order: Order) -> Dict[str, Any]:
        """
        Convert Order model to dictionary.
        
        Args:
            order: Order instance
            
        Returns:
            Dictionary representation
        """
        return {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "product_name": order.product_name,
            "quantity": order.quantity,
            "priority": order.priority,
            "status": order.status,
            "order_placed_at": order.order_placed_at,
            "order_confirmed_at": order.order_confirmed_at,
            "processing_completed_at": order.processing_completed_at,
            "shipped_at": order.shipped_at,
            "delivered_at": order.delivered_at,
        }


# Singleton instance
order_service = OrderService()
