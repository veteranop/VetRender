#!/usr/bin/env python3

import requests
import json

# Test the FCC API directly for KDPI 88.5 FM
print("Testing FCC API directly for KDPI 88.5 FM")
print("=" * 50)

# KDPI coordinates (Ketchum, ID)
lat = 43.6807
lon = -114.3637
frequency = 88.5
radius_km = 10

# API endpoint
api_url = "https://publicfiles.fcc.gov/api/service/fm/facility/search.json"

# Parameters
params = {
    'latitude': lat,
    'longitude': lon,
    'searchRadius': radius_km,
    'frequency': frequency
}

print(f"API URL: {api_url}")
print(f"Parameters: {params}")
print()

try:
    print("Making request...")
    response = requests.get(api_url, params=params, timeout=15)

    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response URL: {response.url}")
    print()

    if response.status_code == 200:
        print("SUCCESS: API responded with 200")
        try:
            data = response.json()
            print("Response type:", type(data))
            print("Response keys:", list(data.keys()) if isinstance(data, dict) else "N/A")

            if isinstance(data, dict) and 'results' in data and 'facilities' in data['results']:
                facilities = data['results']['facilities']
                print(f"Found {len(facilities)} facilities")

                # Look for KDPI
                kdpi_found = False
                for facility in facilities:
                    call_sign = facility.get('callSign', '')
                    if call_sign == 'KDPI':
                        kdpi_found = True
                        print("KDPI FOUND!")
                        print(json.dumps(facility, indent=2))
                        break

                if not kdpi_found:
                    print("KDPI not found in results")
                    if facilities:
                        print("First facility found:")
                        print(json.dumps(facilities[0], indent=2))

            else:
                print("Unexpected response structure:")
                print(json.dumps(data, indent=2)[:500])

        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print("Raw response (first 500 chars):")
            print(response.text[:500])

    elif response.status_code == 404:
        print("ERROR: 404 Not Found - API endpoint may not exist")
        print("Response headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

    else:
        print(f"ERROR: HTTP {response.status_code}")
        print("Response:", response.text[:200])

except requests.exceptions.Timeout:
    print("ERROR: Request timed out")

except requests.exceptions.RequestException as e:
    print(f"ERROR: Request failed - {e}")

except Exception as e:
    print(f"ERROR: Unexpected error - {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test completed")