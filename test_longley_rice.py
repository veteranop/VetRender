"""
Test script for Longley-Rice propagation model in VetRender
============================================================

This script tests the new Longley-Rice implementation independently.

USAGE:
    python test_longley_rice.py

VALIDATION:
- Compare results with known propagation tools
- Check for reasonable loss values
- Verify error handling

ROLLBACK: Delete this file when Longley-Rice is validated
"""

import sys
import os

# Add VetRender to path
sys.path.insert(0, os.path.dirname(__file__))

from models.propagation import PropagationModel

def test_longley_rice():
    """Test Longley-Rice calculations with sample data"""

    print("Testing Longley-Rice Propagation Model")
    print("="*50)

    # Test parameters (similar to KDPI)
    test_cases = [
        {"distance_km": 1.0, "freq_mhz": 88.5, "tx_height": 2.0, "rx_height": 1.5, "expected_range": (80, 120)},
        {"distance_km": 10.0, "freq_mhz": 88.5, "tx_height": 50.0, "rx_height": 1.5, "expected_range": (100, 140)},
        {"distance_km": 50.0, "freq_mhz": 88.5, "tx_height": 100.0, "rx_height": 1.5, "expected_range": (120, 160)},
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Distance: {case['distance_km']} km")
        print(f"  Frequency: {case['freq_mhz']} MHz")
        print(f"  TX Height: {case['tx_height']} m")
        print(f"  RX Height: {case['rx_height']} m")

        try:
            loss_db = PropagationModel.longley_rice_loss(
                distance_km=case['distance_km'],
                frequency_mhz=case['freq_mhz'],
                tx_height_m=case['tx_height'],
                rx_height_m=case['rx_height']
            )

            print(f"  Loss: {loss_db:.2f} dB")

            # Basic validation
            if case['expected_range'][0] <= loss_db <= case['expected_range'][1]:
                print("  ✓ Within expected range")
            else:
                print(f"  ⚠ Outside expected range {case['expected_range']}")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Test error handling
    print("
Error Handling Tests:")
    try:
        PropagationModel.longley_rice_loss(0, 88.5, 50, 1.5)  # Zero distance
        print("  ✗ Should have failed for zero distance")
    except:
        print("  ✓ Correctly handled zero distance")

    try:
        PropagationModel.longley_rice_loss(10, 1e6, 50, 1.5)  # Invalid frequency
        print("  ✗ Should have failed for invalid frequency")
    except:
        print("  ✓ Correctly handled invalid frequency")

    print("\nTest completed. Review output for validation.")

if __name__ == "__main__":
    test_longley_rice()