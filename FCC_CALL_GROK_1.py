#!/usr/bin/env python3
"""
FCC API Test Script - FCC_CALL_GROK_1.py
========================================
Simple script to test FCC facility search API for KDPI 88.5 FM
"""

import requests
import json
import sys

def test_fcc_api():
    """Test the FCC API for KDPI 88.5 FM"""

    print("FCC API Test for KDPI 88.5 FM")
    print("=" * 50)

    # KDPI coordinates (Ketchum, ID)
    lat = 43.6807
    lon = -114.3637
    frequency = 88.5
    radius_km = 10

    # API endpoint
    api_url = "https://publicfiles.fcc.gov/api/service/fm/facility/search.json"

    # Parameters (try both radius and searchRadius)
    params_variants = [
        {
            'latitude': lat,
            'longitude': lon,
            'radius': radius_km,
            'frequency': frequency
        },
        {
            'latitude': lat,
            'longitude': lon,
            'searchRadius': radius_km,
            'frequency': frequency
        }
    ]

    for i, params in enumerate(params_variants, 1):
        print(f"\nTest {i}: {api_url}")
        print(f"Parameters: {params}")

        try:
            response = requests.get(api_url, params=params, timeout=15)

            print(f"Status: {response.status_code}")
            print(f"URL: {response.url}")

            if response.status_code == 200:
                print("✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"Response type: {type(data)}")

                    if isinstance(data, dict) and 'results' in data:
                        facilities = data['results'].get('facilities', [])
                        print(f"Found {len(facilities)} facilities")

                        # Look for KDPI
                        for facility in facilities:
                            if facility.get('callSign') == 'KDPI':
                                print("🎯 KDPI FOUND!")
                                print(json.dumps(facility, indent=2))
                                return True

                        if facilities:
                            print("Other facilities found:")
                            for facility in facilities[:3]:  # Show first 3
                                print(f"  {facility.get('callSign', 'Unknown')} - {facility.get('city', '')}, {facility.get('state', '')}")
                        else:
                            print("No facilities in results")

                    else:
                        print("Unexpected response structure")
                        print(json.dumps(data, indent=2)[:500])

                except json.JSONDecodeError:
                    print("❌ Failed to parse JSON")
                    print("Raw response:")
                    print(response.text[:500])

            elif response.status_code == 404:
                print("❌ 404 Not Found - API may not exist")
            else:
                print(f"❌ HTTP {response.status_code}")
                print(response.text[:200])

        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 30)

    print("\n" + "=" * 50)
    print("If all tests failed, the FCC API may be unavailable.")
    print("Try these alternatives:")
    print("• FCC Facility Search: https://www.fcc.gov/media/radio/am-fm-tv-and-translator-search")
    print("• FCCData.org: https://www.fccdata.org")
    return False

if __name__ == "__main__":
    success = test_fcc_api()
    sys.exit(0 if success else 1)