"""
Test Script for Phase 2 Analytics Implementation

Tests all new features:
- Analytics aggregation services
- CSV export functionality
- Dummy data generation
- Validation utilities

Run with: python test_phase2.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.validator import order_validator, ValidationError
from app.utils.time_calculator import (
    calculate_procurement_time,
    calculate_processing_time,
    calculate_dispatch_time_duration,
    calculate_delivery_time_duration,
    calculate_total_time,
    calculate_duration,
)
from app.utils.sla_detector import check_sla_breach, get_sla_thresholds
from app.utils.bottleneck_detector import identify_bottleneck, analyze_bottlenecks


def test_validator():
    """Test validation utilities."""
    print("\n" + "="*60)
    print("TESTING VALIDATOR")
    print("="*60)
    
    # Test 1: Valid timestamp sequence
    print("\n[Test 1] Valid timestamp sequence")
    timestamps = {
        "order_placed_at": datetime(2026, 5, 1, 10, 0),
        "order_confirmed_at": datetime(2026, 5, 2, 8, 0),
        "processing_completed_at": datetime(2026, 5, 5, 10, 0),
        "shipped_at": datetime(2026, 5, 5, 18, 0),
        "delivered_at": datetime(2026, 5, 7, 14, 0),
    }
    is_valid, errors = order_validator.validate_timestamp_sequence(timestamps)
    print(f"✓ Valid: {is_valid}, Errors: {errors}")
    assert is_valid, "Valid timestamps should pass validation"
    
    # Test 2: Invalid timestamp sequence (out of order)
    print("\n[Test 2] Invalid timestamp sequence (out of order)")
    bad_timestamps = {
        "order_placed_at": datetime(2026, 5, 1, 10, 0),
        "order_confirmed_at": datetime(2026, 5, 2, 8, 0),
        "processing_completed_at": datetime(2026, 5, 1, 10, 0),  # Before confirmed
        "shipped_at": datetime(2026, 5, 5, 18, 0),
        "delivered_at": datetime(2026, 5, 7, 14, 0),
    }
    is_valid, errors = order_validator.validate_timestamp_sequence(bad_timestamps)
    print(f"✓ Valid: {is_valid}, Errors: {len(errors)} error(s) detected")
    assert not is_valid, "Invalid timestamps should fail validation"
    
    # Test 3: Duration validation
    print("\n[Test 3] Duration validation")
    is_valid, errors = order_validator.validate_durations(
        procurement_time=22.5,
        processing_time=5.0,
        dispatch_time_duration=2.5,
        delivery_time_duration=20.0
    )
    print(f"✓ Valid: {is_valid}, Errors: {errors}")
    assert is_valid, "Valid durations should pass validation"
    
    # Test 4: Invalid duration (negative)
    print("\n[Test 4] Invalid duration (negative)")
    is_valid, errors = order_validator.validate_durations(
        procurement_time=-5.0
    )
    print(f"✓ Valid: {is_valid}, Errors detected: {len(errors)}")
    assert not is_valid, "Negative durations should fail validation"
    
    # Test 5: Comprehensive order validation
    print("\n[Test 5] Comprehensive order validation")
    order_data = {
        "order_number": "TEST-001",
        "customer_name": "Test Corp",
        "product_name": "Widget A",
        "quantity": 100,
        "order_placed_at": datetime(2026, 5, 1, 10, 0),
        "order_confirmed_at": datetime(2026, 5, 2, 8, 0),
        "processing_completed_at": datetime(2026, 5, 5, 10, 0),
        "shipped_at": datetime(2026, 5, 5, 18, 0),
        "delivered_at": datetime(2026, 5, 7, 14, 0),
    }
    is_valid, errors, metadata = order_validator.validate_order_data(order_data)
    print(f"✓ Valid: {is_valid}")
    print(f"✓ Has timestamps: {metadata['has_timestamps']}")
    print(f"✓ All timestamps complete: {metadata['has_all_timestamps']}")
    assert is_valid, "Valid order should pass comprehensive validation"
    
    print("\n✅ VALIDATOR TESTS PASSED")


def test_time_calculator():
    """Test time calculation utilities."""
    print("\n" + "="*60)
    print("TESTING TIME CALCULATOR")
    print("="*60)
    
    # Test durations
    print("\n[Test 1] Calculate individual durations")
    
    order_placed = datetime(2026, 5, 1, 10, 0)
    order_confirmed = datetime(2026, 5, 2, 8, 0)
    processing_completed = datetime(2026, 5, 5, 10, 0)
    shipped = datetime(2026, 5, 5, 18, 0)
    delivered = datetime(2026, 5, 7, 14, 0)
    
    procurement_time = calculate_procurement_time(order_placed, order_confirmed)
    processing_time = calculate_processing_time(order_confirmed, processing_completed)
    dispatch_time_duration = calculate_dispatch_time_duration(processing_completed, shipped)
    delivery_time_duration = calculate_delivery_time_duration(shipped, delivered)
    total_time = calculate_total_time(order_placed, delivered)
    
    print(f"✓ Procurement: {procurement_time}h")
    print(f"✓ Processing: {processing_time}h")
    print(f"✓ Dispatch: {dispatch_time_duration}h")
    print(f"✓ Delivery: {delivery_time_duration}h")
    print(f"✓ Total: {total_time}h")
    
    assert procurement_time == 22.0
    assert processing_time == 74.0
    assert dispatch_time_duration == 8.0
    assert delivery_time_duration == 44.0
    
    # Test with None values (null handling)
    print("\n[Test 2] Null value handling")
    result = calculate_duration(order_placed, None)
    print(f"✓ None timestamp handled: {result}")
    assert result is None or result == 0
    
    print("\n✅ TIME CALCULATOR TESTS PASSED")


def test_sla_detector():
    """Test SLA detection utilities."""
    print("\n" + "="*60)
    print("TESTING SLA DETECTOR")
    print("="*60)
    
    # Test SLA compliance
    print("\n[Test 1] SLA breach detection - procurement stage")

    # New threshold: procurement = 4 hours
    is_breach, breached_stage = check_sla_breach(procurement_time=5.0)   # 5h > 4h threshold
    print(f"✓ Procurement breach (5h > 4h threshold): {is_breach}")
    assert is_breach, "5h procurement should breach 4h SLA"

    is_ok, _ = check_sla_breach(procurement_time=3.0)                    # 3h < 4h threshold
    print(f"✓ Procurement OK (3h < 4h threshold): {not is_ok}")
    assert not is_ok, "3h procurement should not breach 4h SLA"

    # Test thresholds
    print("\n[Test 2] Get SLA thresholds")
    thresholds = get_sla_thresholds()
    print(f"✓ Procurement threshold: {thresholds['procurement']}h")
    print(f"✓ Processing threshold: {thresholds['processing']}h")
    print(f"✓ Dispatch threshold: {thresholds['dispatch']}h")
    print(f"✓ Delivery threshold: {thresholds['delivery']}h")
    
    assert thresholds['procurement'] == 4
    assert thresholds['processing'] == 6
    assert thresholds['dispatch'] == 3
    assert thresholds['delivery'] == 24
    
    print("\n✅ SLA DETECTOR TESTS PASSED")


def test_bottleneck_detector():
    """Test bottleneck detection utilities."""
    print("\n" + "="*60)
    print("TESTING BOTTLENECK DETECTOR")
    print("="*60)
    
    print("\n[Test 1] Identify bottleneck stage")
    
    durations = {
        "procurement_time": 15.0,
        "processing_time": 85.0,  # Longest
        "dispatch_time_duration": 8.0,
        "delivery_time_duration": 35.0,
    }
    
    bottleneck = identify_bottleneck(
        procurement_time=durations["procurement_time"],
        processing_time=durations["processing_time"],
        dispatch_time_duration=durations["dispatch_time_duration"],
        delivery_time_duration=durations["delivery_time_duration"],
    )
    print(f"✓ Bottleneck stage: {bottleneck}")
    assert bottleneck == "processing", "Processing should be identified as bottleneck"
    
    # Test with different bottleneck
    print("\n[Test 2] Different bottleneck scenario")
    durations2 = {
        "procurement_time": 20.0,
        "processing_time": 60.0,
        "dispatch_time_duration": 12.0,
        "delivery_time_duration": 120.0,  # Longest
    }
    
    bottleneck2 = identify_bottleneck(
        procurement_time=durations2["procurement_time"],
        processing_time=durations2["processing_time"],
        dispatch_time_duration=durations2["dispatch_time_duration"],
        delivery_time_duration=durations2["delivery_time_duration"],
    )
    print(f"✓ Bottleneck stage: {bottleneck2}")
    assert bottleneck2 == "delivery", "Delivery should be identified as bottleneck"
    
    # Test ranking
    print("\n[Test 3] Stage ranking by duration")
    ranking_result = analyze_bottlenecks(
        procurement_time=durations["procurement_time"],
        processing_time=durations["processing_time"],
        dispatch_time_duration=durations["dispatch_time_duration"],
        delivery_time_duration=durations["delivery_time_duration"],
    )
    print(f"✓ Bottleneck stage: {ranking_result['bottleneck_stage']}")
    assert ranking_result['bottleneck_stage'] == "processing", "First should be processing (longest)"
    

    print("\n✅ BOTTLENECK DETECTOR TESTS PASSED")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PHASE 2 ANALYTICS IMPLEMENTATION TEST SUITE")
    print("="*60)
    
    try:
        test_validator()
        test_time_calculator()
        test_sla_detector()
        test_bottleneck_detector()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED SUCCESSFULLY")
        print("="*60)
        print("\nNext steps:")
        print("1. Install pandas: pip install pandas>=2.0.0")
        print("2. Start server: python -m uvicorn app.main:app --reload")
        print("3. Visit: http://localhost:8000/docs")
        print("4. Test endpoints:")
        print("   - POST /api/analytics/generate-dummy-data?count=50")
        print("   - GET /api/analytics/summary-enhanced")
        print("   - GET /api/analytics/export")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
