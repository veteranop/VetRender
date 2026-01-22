"""
Test FCC API to verify it's working
"""
import requests
import json

# KDPI station data
lat = 40.54861
lon = -105.0725
frequency = 88.5

print("=" * 80)
print("Testing FCC FM API")
print("=" * 80)
print(f"Station: KDPI 88.5 FM")
print(f"Location: {lat}, {lon}")
print(f"Frequency: {frequency} MHz")
print()

# Test 1: Try the exact API from the code
print("Test 1: Direct API call")
print("-" * 80)
url = 'https://publicfiles.fcc.gov/api/service/fm/facility/search.json'
params = {
    'latitude': lat,
    'longitude': lon,
    'radius': 10,
    'frequency': frequency
}

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Request URL: {response.url}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("Response structure:")
        print(json.dumps(data, indent=2)[:1000])  # First 1000 chars
        print()

        if 'results' in data:
            print(f"Found 'results' key")
            if 'facilities' in data['results']:
                facilities = data['results']['facilities']
                print(f"Found {len(facilities)} facilities")
                if facilities:
                    print("\nFirst facility:")
                    print(json.dumps(facilities[0], indent=2))
            else:
                print("No 'facilities' key in results")
                print(f"Results keys: {list(data['results'].keys())}")
        else:
            print("No 'results' key in response")
            print(f"Response keys: {list(data.keys())}")
    else:
        print(f"HTTP Error: {response.text[:500]}")

except requests.exceptions.RequestException as e:
    print(f"Request Exception: {e}")
except Exception as e:
    print(f"Exception: {e}")

print()
print("=" * 80)

# Test 2: Try without frequency parameter
print("\nTest 2: Search without frequency filter (just lat/lon/radius)")
print("-" * 80)
params2 = {
    'latitude': lat,
    'longitude': lon,
    'radius': 10
}

try:
    response = requests.get(url, params=params2, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Request URL: {response.url}")

    if response.status_code == 200:
        data = response.json()
        if 'results' in data and 'facilities' in data['results']:
            facilities = data['results']['facilities']
            print(f"Found {len(facilities)} facilities within 10km")
            for fac in facilities[:5]:  # Show first 5
                call = fac.get('callSign', 'N/A')
                freq = fac.get('frequency', 'N/A')
                print(f"  - {call} @ {freq} MHz")
except Exception as e:
    print(f"Exception: {e}")

print()
print("=" * 80)
print("Test complete. Run this script to see FCC API response.")
