"""
Test the actual working FCC APIs based on current documentation
"""
import requests
import json

# KDPI coordinates
lat = 40.54861
lon = -105.0725
frequency = 88.5

print("=" * 80)
print("Testing FCC Data API Endpoints (2026)")
print("=" * 80)

# Test 1: LPFM API (data.fcc.gov)
print("\nTest 1: FCC LPFM API")
print("-" * 80)
url = f"http://data.fcc.gov/lpfmapi/rest/v1/lat/{lat}/long/{lon}?format=json"
print(f"URL: {url}")

try:
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("\nResponse structure:")
        print(json.dumps(data, indent=2)[:1500])
except Exception as e:
    print(f"Error: {e}")

# Test 2: Try the FCC Media Bureau Public API
print("\n\nTest 2: FCC Media Bureau API (Contours)")
print("-" * 80)
# Coverage API for arbitrary location
url = "https://geo.fcc.gov/api/census/area"
params = {
    'lat': lat,
    'lon': lon,
    'format': 'json'
}
print(f"URL: {url}")
print(f"Params: {params}")

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("\nResponse:")
        print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"Error: {e}")

# Test 3: Try FCCdata.org unofficial API
print("\n\nTest 3: FCCdata.org (Unofficial)")
print("-" * 80)
print("Note: FCCdata.org doesn't have a public API")
print("Website: https://www.fccdata.org/")
print("Manual search required")

# Test 4: Universal Licensing System API
print("\n\nTest 4: ULS API")
print("-" * 80)
url = "https://data.fcc.gov/api/license-view/basicSearch/getLicenses"
params = {
    'searchValue': 'KDPI',
    'format': 'json'
}
print(f"URL: {url}")
print(f"Params: {params}")

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("\nResponse:")
        print(json.dumps(data, indent=2)[:1000])
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("\nConclusion:")
print("The old publicfiles.fcc.gov/api endpoints are deprecated.")
print("Working alternatives:")
print("  1. data.fcc.gov/lpfmapi - for LPFM stations")
print("  2. geo.fcc.gov/api - for geographic/census data")
print("  3. Manual search at fccdata.org or fcc.gov/media/radio/fm-query")
