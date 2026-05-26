"""
Validation Tests for Analytics Engine

Tests the core analytics utilities to ensure correct calculations.
Run this before starting the server to validate the analytics engine.
"""

from datetime import datetime, timedelta
from app.utils.time_calculator import (
    calculate_duration,
    calculate_procurement_time,
    calculate_processing_time,
    calculate_dispatch_time,
    calculate_delivery_time,
    calculate_total_time,
    calculate_all_durations
)
from app.utils.sla_detector import (
    check_sla_breach,
    get_sla_status,
    get_sla_thresholds
)
from app.utils.bottleneck_detector import (
    identify_bottleneck,
    analyze_bottlenecks
)


def test_time_calculator():
    """Test time calculation utilities."""
    print("=" * 60)
    print("Testing Time Calculator")
    print("=" * 60)
    
    # Test basic duration calculation
    start = datetime(2026, 5, 1, 10, 0, 0)
    end = datetime(2026, 5, 1, 14, 30, 0)
    duration = calculate_duration(start, end)
    
    print(f"\n✓ Basic Duration: {duration} hours")
    assert duration == 4.5, "Duration calculation failed"
    
    # Test negative duration (invalid sequence)
    negative = calculate_duration(end, start)
    print(f"✓ Negative Duration Handling: {negative}")
    assert negative is None, "Negative duration should return None"
    
    # Test None handling
    none_duration = calculate_duration(None, end)
    print(f"✓ None Handling: {none_duration}")
    assert none_duration is None, "None timestamp should return None"
    
    # Test complete lifecycle
    order_placed = datetime(2026, 5, 1, 10, 0, 0)
    order_confirmed = order_placed + timedelta(hours=22)
    processing_completed = order_confirmed + timedelta(hours=70)
    shipped = processing_completed + timedelta(hours=10)
    delivered = shipped + timedelta(hours=45)
    
    timestamps = {
        "order_placed_at": order_placed,
        "order_confirmed_at": order_confirmed,
        "processing_completed_at": processing_completed,
        "shipped_at": shipped,
        "delivered_at": delivered
    }
    
    durations = calculate_all_durations(timestamps)
    print(f"\n✓ All Durations Calculated:")
    for stage, duration in durations.items():
        print(f"  {stage}: {duration} hours")
    
    assert durations["procurement_time"] == 22.0
    assert durations["processing_time"] == 70.0
    assert durations["dispatch_time"] == 10.0
    assert durations["delivery_time"] == 45.0
    assert durations["total_time"] == 147.0
    
    print("\n✅ All time calculator tests passed!\n")


def test_sla_detector():
    """Test SLA detection logic."""
    print("=" * 60)
    print("Testing SLA Detector")
    print("=" * 60)
    
    # Get current thresholds
    thresholds = get_sla_thresholds()
    print(f"\n✓ Current SLA Thresholds:")
    for stage, threshold in thresholds.items():
        print(f"  {stage}: {threshold} hours")
    
    # Test no breach
    no_breach, stage = check_sla_breach(
        procurement_time=20.0,
        processing_time=60.0,
        dispatch_time=10.0,
        delivery_time=40.0
    )
    print(f"\n✓ No Breach Test: breach={no_breach}, stage={stage}")
    assert no_breach == False, "Should not detect breach"
    assert stage is None, "Stage should be None"
    
    # Test procurement breach
    proc_breach, proc_stage = check_sla_breach(
        procurement_time=30.0,  # exceeds 24 hour threshold
        processing_time=60.0,
        dispatch_time=10.0,
        delivery_time=40.0
    )
    print(f"✓ Procurement Breach: breach={proc_breach}, stage={proc_stage}")
    assert proc_breach == True, "Should detect breach"
    assert proc_stage == "procurement", "Should identify procurement"
    
    # Test processing breach
    proc_breach, proc_stage = check_sla_breach(
        procurement_time=20.0,
        processing_time=80.0,  # exceeds 72 hour threshold
        dispatch_time=10.0,
        delivery_time=40.0
    )
    print(f"✓ Processing Breach: breach={proc_breach}, stage={proc_stage}")
    assert proc_breach == True, "Should detect breach"
    assert proc_stage == "processing", "Should identify processing"
    
    # Test dispatch breach
    dispatch_breach, dispatch_stage = check_sla_breach(
        procurement_time=20.0,
        processing_time=60.0,
        dispatch_time=15.0,  # exceeds 12 hour threshold
        delivery_time=40.0
    )
    print(f"✓ Dispatch Breach: breach={dispatch_breach}, stage={dispatch_stage}")
    assert dispatch_breach == True, "Should detect breach"
    assert dispatch_stage == "dispatch", "Should identify dispatch"
    
    # Test delivery breach
    delivery_breach, delivery_stage = check_sla_breach(
        procurement_time=20.0,
        processing_time=60.0,
        dispatch_time=10.0,
        delivery_time=50.0  # exceeds 48 hour threshold
    )
    print(f"✓ Delivery Breach: breach={delivery_breach}, stage={delivery_stage}")
    assert delivery_breach == True, "Should detect breach"
    assert delivery_stage == "delivery", "Should identify delivery"
    
    # Test detailed SLA status
    sla_status = get_sla_status(
        procurement_time=20.0,
        processing_time=80.0,
        dispatch_time=10.0,
        delivery_time=40.0
    )
    print(f"\n✓ Detailed SLA Status:")
    print(f"  Overall Breach: {sla_status['sla_breach']}")
    print(f"  Breached Stage: {sla_status['breached_stage']}")
    print(f"  Stage Details:")
    for stage, details in sla_status['stage_details'].items():
        print(f"    {stage}: {details['duration']}h (threshold: {details['threshold']}h) - Breach: {details['breached']}")
    
    print("\n✅ All SLA detector tests passed!\n")


def test_bottleneck_detector():
    """Test bottleneck detection logic."""
    print("=" * 60)
    print("Testing Bottleneck Detector")
    print("=" * 60)
    
    # Test normal case
    bottleneck = identify_bottleneck(
        procurement_time=20.0,
        processing_time=80.0,  # highest
        dispatch_time=10.0,
        delivery_time=40.0
    )
    print(f"\n✓ Bottleneck Identification: {bottleneck}")
    assert bottleneck == "processing", "Should identify processing as bottleneck"
    
    # Test with delivery as bottleneck
    bottleneck2 = identify_bottleneck(
        procurement_time=15.0,
        processing_time=50.0,
        dispatch_time=8.0,
        delivery_time=60.0  # highest
    )
    print(f"✓ Bottleneck (Delivery): {bottleneck2}")
    assert bottleneck2 == "delivery", "Should identify delivery as bottleneck"
    
    # Test with None values
    bottleneck3 = identify_bottleneck(
        procurement_time=20.0,
        processing_time=None,
        dispatch_time=10.0,
        delivery_time=40.0
    )
    print(f"✓ Bottleneck (with None): {bottleneck3}")
    assert bottleneck3 == "delivery", "Should handle None values"
    
    # Test detailed analysis
    analysis = analyze_bottlenecks(
        procurement_time=20.0,
        processing_time=80.0,
        dispatch_time=10.0,
        delivery_time=40.0
    )
    print(f"\n✓ Detailed Bottleneck Analysis:")
    print(f"  Bottleneck Stage: {analysis['bottleneck_stage']}")
    print(f"  Bottleneck Duration: {analysis['bottleneck_duration']} hours")
    print(f"  Total Duration: {analysis['total_duration']} hours")
    print(f"  Stage Percentages:")
    for stage, pct in analysis['stage_percentages'].items():
        print(f"    {stage}: {pct}%")
    
    assert analysis['bottleneck_stage'] == "processing"
    assert analysis['bottleneck_duration'] == 80.0
    assert analysis['total_duration'] == 150.0
    
    print("\n✅ All bottleneck detector tests passed!\n")


def test_preprocessing_pipeline():
    """Test complete preprocessing pipeline."""
    print("=" * 60)
    print("Testing Preprocessing Pipeline")
    print("=" * 60)
    
    from app.services.order_preprocessing import OrderPreprocessor
    
    preprocessor = OrderPreprocessor()
    
    # Sample order data
    order_data = {
        "id": 1,
        "order_number": "ORD-TEST-001",
        "customer_name": "Test Customer",
        "order_placed_at": datetime(2026, 5, 1, 10, 0, 0),
        "order_confirmed_at": datetime(2026, 5, 2, 8, 0, 0),  # 22 hours
        "processing_completed_at": datetime(2026, 5, 5, 10, 0, 0),  # 74 hours (breach!)
        "shipped_at": datetime(2026, 5, 5, 18, 0, 0),  # 8 hours
        "delivered_at": datetime(2026, 5, 7, 14, 0, 0),  # 44 hours
    }
    
    # Process order
    processed = preprocessor.process_order(order_data)
    
    print(f"\n✓ Processed Order:")
    print(f"  Order: {processed['order_number']}")
    print(f"  Procurement Time: {processed['procurement_time']} hours")
    print(f"  Processing Time: {processed['processing_time']} hours")
    print(f"  Dispatch Time: {processed['dispatch_time']} hours")
    print(f"  Delivery Time: {processed['delivery_time']} hours")
    print(f"  Total Time: {processed['total_time']} hours")
    print(f"  SLA Breach: {processed['sla_breach']}")
    print(f"  Breached Stage: {processed['breached_stage']}")
    print(f"  Bottleneck: {processed['bottleneck_stage']}")
    
    assert processed['procurement_time'] == 22.0
    assert processed['processing_time'] == 74.0
    assert processed['dispatch_time'] == 8.0
    assert processed['delivery_time'] == 44.0
    assert processed['total_time'] == 148.0
    assert processed['sla_breach'] == True
    assert processed['breached_stage'] == "processing"
    assert processed['bottleneck_stage'] == "processing"
    
    print("\n✅ Preprocessing pipeline test passed!\n")


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("SUPPLY CHAIN ANALYTICS ENGINE - VALIDATION TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_time_calculator()
        test_sla_detector()
        test_bottleneck_detector()
        test_preprocessing_pipeline()
        
        print("=" * 60)
        print("✅ ALL VALIDATION TESTS PASSED!")
        print("=" * 60)
        print("\nThe analytics engine is working correctly.")
        print("You can now start the server with: uvicorn app.main:app --reload\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
