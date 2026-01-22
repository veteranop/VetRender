#!/usr/bin/env python3
"""
Scan FCC Developer Documentation
=================================
Check available FCC APIs and their status
"""

import requests
from bs4 import BeautifulSoup
import json

def scan_fcc_developer():
    """Scan the FCC developer documentation page"""

    print("Scanning FCC Developer Documentation")
    print("=" * 50)

    developer_url = "https://publicfiles.fcc.gov/developer"

    try:
        print(f"Accessing: {developer_url}")
        response = requests.get(developer_url, timeout=15)

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Page accessible")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for API documentation
            print("\nScanning for API information...")

            # Check for facility search APIs
            facility_apis = [
                "facility/search",
                "broadcast",
                "facility",
                "fm",
                "am",
                "tv"
            ]

            api_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()

                # Check if it's an API-related link
                if any(api_term in href.lower() or api_term in text.lower() for api_term in facility_apis):
                    api_links.append({
                        'url': href if href.startswith('http') else f"https://publicfiles.fcc.gov{href}",
                        'text': text
                    })

            if api_links:
                print(f"Found {len(api_links)} potential API links:")
                for api in api_links[:10]:  # Show first 10
                    print(f"  • {api['text']}: {api['url']}")
            else:
                print("No facility API links found on page")

            # Look for API status or notices
            alerts = soup.find_all(['div', 'p'], class_=lambda x: x and ('alert' in x or 'warning' in x or 'error' in x))
            if alerts:
                print("\n⚠️  Found alerts/notices:")
                for alert in alerts[:3]:
                    print(f"  {alert.get_text().strip()[:200]}...")

            # Check for JSON API endpoints mentioned
            json_apis = soup.find_all(text=lambda x: x and ('api/service' in x or '.json' in x))
            if json_apis:
                print("\n📋 JSON API endpoints mentioned:")
                for api_text in json_apis[:5]:
                    print(f"  {api_text.strip()[:100]}")

        else:
            print(f"❌ Page not accessible (HTTP {response.status_code})")

    except Exception as e:
        print(f"❌ Error accessing page: {e}")

    print("\n" + "=" * 50)

    # Test some known FCC API endpoints
    print("Testing known FCC API endpoints...")

    test_endpoints = [
        "https://publicfiles.fcc.gov/api/service/fm/facility/search.json",
        "https://data.fcc.gov/resource/4rw4-7xhp.json",
        "https://www.fcc.gov/developers/broadcast-facility-data-api"
    ]

    for endpoint in test_endpoints:
        try:
            print(f"\nTesting: {endpoint}")
            response = requests.head(endpoint, timeout=10)  # Use HEAD to check if exists
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  ✅ Accessible")
            elif response.status_code == 404:
                print("  ❌ 404 Not Found")
            else:
                print(f"  ⚠️  HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    scan_fcc_developer()