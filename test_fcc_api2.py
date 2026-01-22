"""
Test different FCC API endpoints to find the working one
"""
import requests
import json

# KDPI call sign
call_sign = "KDPI"

print("=" * 80)
print("Testing FCC API Endpoints")
print("=" * 80)

# Try different API endpoints
endpoints_to_test = [
    # New FCC API (might be CDBS)
    f"https://publicfiles.fcc.gov/api/manager/download/facility/{call_sign}/search",

    # Try direct call sign lookup
    f"https://publicfiles.fcc.gov/api/service/fm/call-sign/{call_sign}.json",

    # Try the LMS API (License Management System)
    "https://data.fcc.gov/api/license-view/basicSearch/getLicenses",

    # Try the ULS API
    "https://wireless2.fcc.gov/UlsApp/UlsSearch/searchLicense.jsp",
]

for i, url in enumerate(endpoints_to_test, 1):
    print(f"\nTest {i}: {url}")
    print("-" * 80)

    try:
        if "data.fcc.gov" in url:
            # Try LMS API with call sign
            params = {'searchValue': call_sign}
            response = requests.get(url, params=params, timeout=10)
        else:
            response = requests.get(url, timeout=10)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("SUCCESS!")
            try:
                data = response.json()
                print("Response preview:")
                print(json.dumps(data, indent=2)[:500])
            except:
                print("Response (not JSON):")
                print(response.text[:500])
        else:
            print(f"Failed: {response.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

# Try the FCC's CDBS database directly
print("\n" + "=" * 80)
print("Trying FCC CDBS Public API")
print("=" * 80)

# CDBS uses facility IDs - we need to search by call sign first
# Try the FCC's general search API
url = "https://publicfiles.fcc.gov/api/service/fm/search.json"
print(f"\nURL: {url}")

try:
    params = {'callsign': call_sign}
    response = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Request URL: {response.url}")

    if response.status_code == 200:
        data = response.json()
        print("\nResponse:")
        print(json.dumps(data, indent=2)[:1000])
    else:
        print(f"Error: {response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "=" * 80)
print("\nRecommendation: The FCC changed their public API structure.")
print("Best approach: Use FCC's Application Search or manual entry.")
print("Alternative: Scrape from https://fccdata.org or use commercial API")
