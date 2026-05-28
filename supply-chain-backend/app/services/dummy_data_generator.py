"""
Dummy Data Generator Service

Generates realistic supply chain order data for testing and demonstration.
Creates diverse scenarios including:
- Normal orders with standard durations
- SLA breaches on various stages
- Different bottleneck patterns
- Various priority levels and customer types
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session

from app.models import Order, OrderStatus as ModelOrderStatus
from app.services.order_preprocessing import default_preprocessor


class DummyDataGenerator:
    """Service for generating realistic dummy supply chain data."""
    
    # Sample data for generating variety
    CUSTOMER_NAMES = [
        "Acme Corporation",
        "TechFlow Industries",
        "GlobalMart Retail",
        "SmallBiz Solutions",
        "Enterprise Logistics",
        "Premier Manufacturing",
        "Swift Distribution",
        "Quality Trading Co",
        "StandardPart Supplies",
        "PrecisionCraft Inc",
    ]
    
    PRODUCTS = [
        "Industrial Widget A",
        "Premium Widget B",
        "Standard Component X",
        "Advanced Sensor Z",
        "Connector Assembly",
        "Control Unit Pro",
        "Power Module",
        "Interface Card",
        "Processing Unit",
        "Storage Device",
    ]
    
    PRIORITIES = ["normal", "high", "urgent"]
    
    # Duration ranges in hours (realistic supply chain times)
    DURATION_RANGES = {
        "procurement_normal": (12, 36),      # 12-36 hours normal
        "procurement_breach": (36, 72),      # 36-72 hours (breach after 24h)
        
        "processing_normal": (48, 96),       # 2-4 days normal
        "processing_breach": (96, 168),      # 4-7 days (breach after 72h)
        
        "dispatch_normal": (6, 18),          # 6-18 hours normal
        "dispatch_breach": (18, 48),         # 18-48 hours (breach after 12h)
        
        "delivery_normal": (24, 72),         # 1-3 days normal
        "delivery_breach": (72, 144),        # 3-6 days (breach after 48h)
    }
    
    @staticmethod
    def _generate_order_number(index: int) -> str:
        """Generate unique order number."""
        return f"ORD-GEN-{datetime.now().strftime('%Y%m%d')}-{index:04d}"
    
    @staticmethod
    def _generate_customer_email(customer_name: str) -> str:
        """Generate email from customer name."""
        domain = random.choice(["company.com", "business.org", "trade.net", "supply.io"])
        name_part = customer_name.lower().replace(" ", "")[:10]
        return f"{name_part}@{domain}"
    
    @staticmethod
    def _generate_realistic_durations() -> Tuple[float, float, float, float]:
        """
        Generate realistic duration combinations with various scenarios.
        
        Returns:
            Tuple of (procurement, processing, dispatch, delivery) in hours
        """
        scenario = random.choices(
            population=[
                "normal",           # All stages normal
                "bottleneck_proc",  # Procurement bottleneck
                "bottleneck_proc_time",  # Processing bottleneck
                "bottleneck_dispatch",   # Dispatch bottleneck
                "bottleneck_delivery",   # Delivery bottleneck
                "sla_breach_proc",  # Processing SLA breach
                "sla_breach_delivery",   # Delivery SLA breach
                "multiple_issues",  # Multiple delays
            ],
            weights=[30, 15, 20, 15, 10, 5, 2, 3]  # Probabilities
        )[0]
        
        if scenario == "normal":
            procurement = random.uniform(*DummyDataGenerator.DURATION_RANGES["procurement_normal"])
            processing = random.uniform(*DummyDataGenerator.DURATION_RANGES["processing_normal"])
            dispatch = random.uniform(*DummyDataGenerator.DURATION_RANGES["dispatch_normal"])
            delivery = random.uniform(*DummyDataGenerator.DURATION_RANGES["delivery_normal"])
        
        elif scenario == "bottleneck_proc":
            procurement = random.uniform(60, 120)  # Very long procurement
            processing = random.uniform(*DummyDataGenerator.DURATION_RANGES["processing_normal"])
            dispatch = random.uniform(*DummyDataGenerator.DURATION_RANGES["dispatch_normal"])
            delivery = random.uniform(*DummyDataGenerator.DURATION_RANGES["delivery_normal"])
        
        elif scenario == "bottleneck_proc_time":
            procurement = random.uniform(*DummyDataGenerator.DURATION_RANGES["procurement_normal"])
            processing = random.uniform(120, 192)  # Very long processing
            dispatch = random.uniform(*DummyDataGenerator.DURATION_RANGES["dispatch_normal"])
            delivery = random.uniform(*DummyDataGenerator.DURATION_RANGES["delivery_normal"])
        
        elif scenario == "bottleneck_dispatch":
            procurement = random.uniform(*DummyDataGenerator.DURATION_RANGES["procurement_normal"])
            processing = random.uniform(*DummyDataGenerator.DURATION_RANGES["processing_normal"])
            dispatch = random.uniform(36, 72)  # Very long dispatch
            delivery = random.uniform(*DummyDataGenerator.DURATION_RANGES["delivery_normal"])
        
        elif scenario == "bottleneck_delivery":
            procurement = random.uniform(*DummyDataGenerator.DURATION_RANGES["procurement_normal"])
            processing = random.uniform(*DummyDataGenerator.DURATION_RANGES["processing_normal"])
            dispatch = random.uniform(*DummyDataGenerator.DURATION_RANGES["dispatch_normal"])
            delivery = random.uniform(120, 240)  # Very long delivery
        
        elif scenario == "sla_breach_proc":
            procurement = random.uniform(*DummyDataGenerator.DURATION_RANGES["procurement_normal"])
            processing = random.uniform(*DummyDataGenerator.DURATION_RANGES["processing_breach"])
            dispatch = random.uniform(*DummyDataGenerator.DURATION_RANGES["dispatch_normal"])
            delivery = random.uniform(*DummyDataGenerator.DURATION_RANGES["delivery_normal"])
        
        elif scenario == "sla_breach_delivery":
            procurement = random.uniform(*DummyDataGenerator.DURATION_RANGES["procurement_normal"])
            processing = random.uniform(*DummyDataGenerator.DURATION_RANGES["processing_normal"])
            dispatch = random.uniform(*DummyDataGenerator.DURATION_RANGES["dispatch_normal"])
            delivery = random.uniform(*DummyDataGenerator.DURATION_RANGES["delivery_breach"])
        
        else:  # multiple_issues
            procurement = random.uniform(30, 50)
            processing = random.uniform(100, 150)
            dispatch = random.uniform(15, 30)
            delivery = random.uniform(80, 120)
        
        return round(procurement, 2), round(processing, 2), round(dispatch, 2), round(delivery, 2)
    
    @staticmethod
    def generate_orders(count: int = 200) -> List[Dict[str, Any]]:
        """
        Generate realistic dummy orders.
        
        Args:
            count: Number of orders to generate
            
        Returns:
            List of order dictionaries
        """
        orders = []
        
        # Use current time as base
        base_time = datetime.now() - timedelta(days=90)  # Start from 90 days ago
        
        for i in range(count):
            # Generate dates spread over the period
            order_placed = base_time + timedelta(
                days=random.randint(0, 89),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Generate realistic durations
            proc_time, proc_time_dur, dispatch_time, delivery_time = DummyDataGenerator._generate_realistic_durations()
            
            # Calculate timestamps from durations
            order_confirmed = order_placed + timedelta(hours=proc_time)
            processing_completed = order_confirmed + timedelta(hours=proc_time_dur)
            shipped = processing_completed + timedelta(hours=dispatch_time)
            delivered = shipped + timedelta(hours=delivery_time)
            
            order_data = {
                "order_number": DummyDataGenerator._generate_order_number(i + 1),
                "customer_name": random.choice(DummyDataGenerator.CUSTOMER_NAMES),
                "customer_email": None,  # Will be generated from customer name
                "product_name": random.choice(DummyDataGenerator.PRODUCTS),
                "quantity": random.randint(1, 500),
                "priority": random.choice(DummyDataGenerator.PRIORITIES),
                "status": ModelOrderStatus.COMPLETED,
                
                # Lifecycle timestamps
                "order_placed_at": order_placed,
                "order_confirmed_at": order_confirmed,
                "processing_completed_at": processing_completed,
                "shipped_at": shipped,
                "delivered_at": delivered,
            }
            
            # Generate email
            order_data["customer_email"] = DummyDataGenerator._generate_customer_email(
                order_data["customer_name"]
            )
            
            orders.append(order_data)
        
        return orders
    
    @staticmethod
    def seed_orders_data(db: Session, count: int = 200) -> Dict[str, Any]:
        """
        Generate and insert dummy orders into database.
        
        Args:
            db: Database session
            count: Number of orders to generate
            
        Returns:
            Summary of inserted data
        """
        # Generate orders
        orders_data = DummyDataGenerator.generate_orders(count)
        
        # Track statistics
        inserted_count = 0
        sla_breaches = 0
        bottleneck_stages = {}
        
        # Insert orders through preprocessing pipeline
        for order_data in orders_data:
            try:
                # Run through preprocessing pipeline
                processed_data = default_preprocessor.process_order(order_data)
                
                # Create order instance
                db_order = Order(
                    order_number=processed_data.get("order_number"),
                    customer_name=processed_data.get("customer_name"),
                    customer_email=processed_data.get("customer_email"),
                    product_name=processed_data.get("product_name"),
                    quantity=processed_data.get("quantity"),
                    priority=processed_data.get("priority", "normal"),
                    status=processed_data.get("status", ModelOrderStatus.COMPLETED),
                    
                    # Lifecycle timestamps
                    order_placed_at=processed_data.get("order_placed_at"),
                    order_confirmed_at=processed_data.get("order_confirmed_at"),
                    processing_completed_at=processed_data.get("processing_completed_at"),
                    shipped_at=processed_data.get("shipped_at"),
                    delivered_at=processed_data.get("delivered_at"),
                    
                    # Analytics fields
                    procurement_time=processed_data.get("procurement_time"),
                    processing_time=processed_data.get("processing_time"),
                    dispatch_time=processed_data.get("dispatch_time"),
                    delivery_time=processed_data.get("delivery_time"),
                    total_time=processed_data.get("total_time"),
                    sla_breach=processed_data.get("sla_breach", False),
                    breached_stage=processed_data.get("breached_stage"),
                    bottleneck_stage=processed_data.get("bottleneck_stage"),
                )
                
                db.add(db_order)
                inserted_count += 1
                
                # Track statistics
                if processed_data.get("sla_breach"):
                    sla_breaches += 1
                
                bottleneck = processed_data.get("bottleneck_stage")
                if bottleneck:
                    bottleneck_stages[bottleneck] = bottleneck_stages.get(bottleneck, 0) + 1
            
            except Exception as e:
                print(f"Error inserting order {order_data.get('order_number')}: {str(e)}")
                continue
        
        # Commit all inserts
        db.commit()
        
        # Create summary
        summary = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_generated": count,
            "total_inserted": inserted_count,
            "insertion_rate": round((inserted_count / count * 100), 2) if count > 0 else 0,
            "sla_breaches": sla_breaches,
            "sla_breach_rate": round((sla_breaches / inserted_count * 100), 2) if inserted_count > 0 else 0,
            "bottleneck_distribution": bottleneck_stages,
        }
        
        return summary


# Singleton instance
dummy_data_generator = DummyDataGenerator()
