"""
Test the updated FCC API using data.fcc.gov Socrata endpoints
"""
import requests
import json

# KDPI station data (Ketchum/Sun Valley, Idaho)
lat = 43.6807
lon = -114.3637
frequency = 88.5

print("=" * 80)
print("Testing Updated FCC FM API (data.fcc.gov)")
print("=" * 80)
print(f"Station: KDPI 88.5 FM")
print(f"Location: {lat}, {lon} (Ketchum/Sun Valley, ID)")
print(f"Frequency: {frequency} MHz")
print()

# Test the new API
print("Test: New Socrata API")
print("-" * 80)
url = 'https://data.fcc.gov/resource/4rw4-7xhp.json'

# Convert radius to meters (10km)
radius_m = 10 * 1000

# Build SoQL query using lat/lon bounds (with frequency tolerance)
radius_deg = 10 * 0.009  # 10km ≈ 0.09°
lat_min = lat - radius_deg
lat_max = lat + radius_deg
lon_min = lon - radius_deg
lon_max = lon + radius_deg
where_clause = f"latitude >= {lat_min} and latitude <= {lat_max} and longitude >= {lon_min} and longitude <= {lon_max} and frequency >= {frequency - 0.1} and frequency <= {frequency + 0.1}"

params = {
    '$where': where_clause,
    '$limit': 10,
    '$select': 'call_sign,facility_id,frequency,comm_city,comm_state,erp_watts,haat_meters,latitude,longitude'
}

print(f"URL: {url}")
print(f"Where clause: {where_clause}")
print()

try:
    response = requests.get(url, params=params, timeout=15)
    print(f"Status Code: {response.status_code}")
    print(f"Request URL: {response.url}")
    print()

    if response.status_code == 200:
        data = response.json()
        print(f"Response type: {type(data)}")
        print(f"Number of results: {len(data) if isinstance(data, list) else 'N/A'}")
        print()

        if isinstance(data, list) and data:
            print("First facility:")
            print(json.dumps(data[0], indent=2))
            print()

            # Check if KDPI is in results
            kdpi_found = any(f.get('call_sign') == 'KDPI' for f in data)
            print(f"KDPI found in results: {kdpi_found}")
        else:
            print("No data returned or unexpected format")
    else:
        print(f"Error response: {response.text}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)