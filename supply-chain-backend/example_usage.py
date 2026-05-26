"""
Example Usage: Supply Chain Analytics API

This file demonstrates how to use the analytics processing engine.
Includes examples of creating orders with lifecycle data and querying analytics.
"""

import requests
from datetime import datetime, timedelta
import json

# API base URL
BASE_URL = "http://localhost:8000"

# Example 1: Create order with complete lifecycle timestamps
def create_sample_order_with_analytics():
    """
    Create an order with complete lifecycle timestamps.
    The backend will automatically calculate durations, detect SLA breaches, and identify bottlenecks.
    """
    
    # Simulate order lifecycle
    order_placed = datetime(2026, 5, 1, 10, 0, 0)
    order_confirmed = order_placed + timedelta(hours=20)  # 20 hours (within SLA)
    processing_completed = order_confirmed + timedelta(hours=80)  # 80 hours (breaches SLA!)
    shipped = processing_completed + timedelta(hours=8)  # 8 hours
    delivered = shipped + timedelta(hours=45)  # 45 hours
    
    order_data = {
        "order_number": "ORD-2026-001",
        "customer_name": "Acme Corp",
        "customer_email": "orders@acmecorp.com",
        "product_name": "Industrial Widget XL",
        "quantity": 100,
        "priority": "high",
        "status": "completed",
        
        # Lifecycle timestamps (ISO format)
        "order_placed_at": order_placed.isoformat(),
        "order_confirmed_at": order_confirmed.isoformat(),
        "processing_completed_at": processing_completed.isoformat(),
        "shipped_at": shipped.isoformat(),
        "delivered_at": delivered.isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/api/orders/", json=order_data)
    
    if response.status_code == 201:
        order = response.json()
        print("✓ Order created successfully!")
        print(f"  Order ID: {order['id']}")
        print(f"  Order Number: {order['order_number']}")
        print(f"\n  Analytics Results:")
        print(f"    Procurement Time: {order['procurement_time']} hours")
        print(f"    Processing Time: {order['processing_time']} hours")
        print(f"    Dispatch Time: {order['dispatch_time']} hours")
        print(f"    Delivery Time: {order['delivery_time']} hours")
        print(f"    Total Time: {order['total_time']} hours")
        print(f"\n  SLA Breach: {order['sla_breach']}")
        if order['breached_stage']:
            print(f"  Breached Stage: {order['breached_stage']}")
        print(f"  Bottleneck Stage: {order['bottleneck_stage']}")
        
        return order['id']
    else:
        print(f"✗ Error creating order: {response.text}")
        return None


# Example 2: Query analytics summary
def get_analytics_summary():
    """Get aggregate analytics across all orders."""
    response = requests.get(f"{BASE_URL}/api/analytics/summary")
    
    if response.status_code == 200:
        summary = response.json()
        print("\n📊 Analytics Summary:")
        print(f"  Total Orders: {summary['total_orders']}")
        print(f"  SLA Breaches: {summary['sla_breaches']} ({summary['sla_breach_rate']}%)")
        print(f"\n  Average Durations:")
        for stage, duration in summary['average_durations'].items():
            if duration:
                print(f"    {stage.capitalize()}: {duration} hours")
        print(f"\n  Bottleneck Distribution:")
        for stage, count in summary['bottleneck_distribution'].items():
            print(f"    {stage}: {count} orders")
    else:
        print(f"✗ Error: {response.text}")


# Example 3: Get SLA breaches
def get_sla_breach_orders():
    """Get all orders that breached SLA."""
    response = requests.get(f"{BASE_URL}/api/analytics/sla-breaches?limit=5")
    
    if response.status_code == 200:
        orders = response.json()
        print(f"\n⚠️  SLA Breach Report ({len(orders)} orders):")
        for order in orders:
            print(f"\n  Order: {order['order_number']}")
            print(f"    Breached Stage: {order['breached_stage']}")
            print(f"    Total Time: {order['total_time']} hours")
    else:
        print(f"✗ Error: {response.text}")


# Example 4: Get bottleneck analysis
def get_bottleneck_analysis():
    """Get bottleneck distribution and orders by bottleneck."""
    response = requests.get(f"{BASE_URL}/api/analytics/bottleneck-distribution")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🔍 Bottleneck Analysis:")
        print(f"  Total Orders with Bottleneck: {data['total_orders_with_bottleneck']}")
        print(f"\n  Distribution:")
        for item in data['distribution']:
            print(f"    {item['stage']}: {item['count']} orders ({item['percentage']}%)")
    else:
        print(f"✗ Error: {response.text}")


# Example 5: Get stage performance statistics
def get_stage_performance():
    """Get performance statistics for each stage."""
    response = requests.get(f"{BASE_URL}/api/analytics/stage-performance")
    
    if response.status_code == 200:
        performance = response.json()
        print(f"\n📈 Stage Performance Statistics:")
        for stage, stats in performance.items():
            if stats['count'] > 0:
                print(f"\n  {stage.capitalize()}:")
                print(f"    Average: {stats['average']} hours")
                print(f"    Min: {stats['minimum']} hours")
                print(f"    Max: {stats['maximum']} hours")
                print(f"    Sample Size: {stats['count']} orders")
    else:
        print(f"✗ Error: {response.text}")


# Example 6: Get detailed analysis for specific order
def get_order_detailed_analysis(order_id):
    """Get comprehensive analytics report for a specific order."""
    response = requests.get(f"{BASE_URL}/api/analytics/order/{order_id}/detailed-analysis")
    
    if response.status_code == 200:
        analysis = response.json()
        print(f"\n📋 Detailed Analysis for Order {analysis['order_number']}:")
        
        print(f"\n  Durations:")
        for stage, duration in analysis['durations'].items():
            if duration:
                print(f"    {stage}: {duration} hours")
        
        print(f"\n  SLA Status:")
        print(f"    Overall Breach: {analysis['sla_status']['sla_breach']}")
        if analysis['sla_status']['breached_stage']:
            print(f"    Breached Stage: {analysis['sla_status']['breached_stage']}")
        
        print(f"\n  Bottleneck Analysis:")
        ba = analysis['bottleneck_analysis']
        if ba['bottleneck_stage']:
            print(f"    Bottleneck Stage: {ba['bottleneck_stage']}")
            print(f"    Bottleneck Duration: {ba['bottleneck_duration']} hours")
            print(f"    Total Duration: {ba['total_duration']} hours")
            print(f"\n    Stage Percentages:")
            for stage, pct in ba['stage_percentages'].items():
                print(f"      {stage}: {pct}%")
    else:
        print(f"✗ Error: {response.text}")


# Example 7: Filter orders by bottleneck stage
def get_orders_by_bottleneck_stage(stage="processing"):
    """Get orders filtered by specific bottleneck stage."""
    response = requests.get(f"{BASE_URL}/api/analytics/bottlenecks/{stage}?limit=3")
    
    if response.status_code == 200:
        orders = response.json()
        print(f"\n🎯 Orders with {stage.capitalize()} Bottleneck ({len(orders)} orders):")
        for order in orders:
            print(f"\n  {order['order_number']}")
            print(f"    Total Time: {order['total_time']} hours")
            print(f"    {stage.capitalize()} Time: {order[f'{stage}_time']} hours")
    else:
        print(f"✗ Error: {response.text}")


# Example 8: Update order and reprocess analytics
def update_order_timestamps(order_id):
    """Update order timestamps and recalculate analytics."""
    
    # Update shipped timestamp
    new_shipped_time = datetime(2026, 5, 5, 12, 0, 0)
    
    update_data = {
        "shipped_at": new_shipped_time.isoformat()
    }
    
    # reprocess_analytics=true will recalculate all analytics
    response = requests.patch(
        f"{BASE_URL}/api/orders/{order_id}?reprocess_analytics=true",
        json=update_data
    )
    
    if response.status_code == 200:
        order = response.json()
        print(f"\n✓ Order updated and analytics reprocessed!")
        print(f"  New Dispatch Time: {order['dispatch_time']} hours")
        print(f"  New Total Time: {order['total_time']} hours")
        print(f"  SLA Breach: {order['sla_breach']}")
        print(f"  Bottleneck: {order['bottleneck_stage']}")
    else:
        print(f"✗ Error: {response.text}")


# Example 9: Get current SLA thresholds
def get_sla_thresholds():
    """Get current SLA threshold configuration."""
    response = requests.get(f"{BASE_URL}/api/analytics/sla-thresholds")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n⏱️  SLA Thresholds ({data['unit']}):")
        for stage, threshold in data['thresholds'].items():
            print(f"    {stage.capitalize()}: {threshold} hours")
    else:
        print(f"✗ Error: {response.text}")


# Example 10: Create multiple sample orders
def create_multiple_sample_orders():
    """Create multiple orders with varying characteristics for testing."""
    
    base_time = datetime(2026, 5, 1, 10, 0, 0)
    
    orders = [
        {
            "order_number": "ORD-2026-002",
            "customer_name": "TechCo Inc",
            "product_name": "Server Component A",
            "quantity": 50,
            "priority": "normal",
            "procurement": 18,  # hours
            "processing": 60,
            "dispatch": 10,
            "delivery": 40
        },
        {
            "order_number": "ORD-2026-003",
            "customer_name": "GlobalMart",
            "product_name": "Retail Product B",
            "quantity": 200,
            "priority": "urgent",
            "procurement": 12,
            "processing": 90,  # will breach
            "dispatch": 15,  # will breach
            "delivery": 30
        },
        {
            "order_number": "ORD-2026-004",
            "customer_name": "SmallBiz LLC",
            "product_name": "Office Supplies",
            "quantity": 25,
            "priority": "normal",
            "procurement": 22,
            "processing": 48,
            "dispatch": 8,
            "delivery": 65  # will breach
        }
    ]
    
    created_count = 0
    for order_spec in orders:
        order_placed = base_time
        order_confirmed = order_placed + timedelta(hours=order_spec['procurement'])
        processing_completed = order_confirmed + timedelta(hours=order_spec['processing'])
        shipped = processing_completed + timedelta(hours=order_spec['dispatch'])
        delivered = shipped + timedelta(hours=order_spec['delivery'])
        
        order_data = {
            "order_number": order_spec['order_number'],
            "customer_name": order_spec['customer_name'],
            "product_name": order_spec['product_name'],
            "quantity": order_spec['quantity'],
            "priority": order_spec['priority'],
            "order_placed_at": order_placed.isoformat(),
            "order_confirmed_at": order_confirmed.isoformat(),
            "processing_completed_at": processing_completed.isoformat(),
            "shipped_at": shipped.isoformat(),
            "delivered_at": delivered.isoformat()
        }
        
        response = requests.post(f"{BASE_URL}/api/orders/", json=order_data)
        if response.status_code == 201:
            created_count += 1
            print(f"✓ Created: {order_spec['order_number']}")
        else:
            print(f"✗ Failed: {order_spec['order_number']}")
    
    print(f"\n✓ Created {created_count} orders")


if __name__ == "__main__":
    print("=" * 60)
    print("Supply Chain Analytics API - Example Usage")
    print("=" * 60)
    
    # Run examples
    print("\n1. Creating sample order with analytics...")
    order_id = create_sample_order_with_analytics()
    
    if order_id:
        print("\n2. Getting analytics summary...")
        get_analytics_summary()
        
        print("\n3. Getting SLA threshold configuration...")
        get_sla_thresholds()
        
        print("\n4. Getting detailed analysis for order...")
        get_order_detailed_analysis(order_id)
        
        print("\n5. Creating multiple sample orders...")
        create_multiple_sample_orders()
        
        print("\n6. Getting updated analytics summary...")
        get_analytics_summary()
        
        print("\n7. Getting SLA breach report...")
        get_sla_breach_orders()
        
        print("\n8. Getting bottleneck analysis...")
        get_bottleneck_analysis()
        
        print("\n9. Getting stage performance statistics...")
        get_stage_performance()
        
        print("\n" + "=" * 60)
        print("✓ All examples completed!")
        print("=" * 60)
