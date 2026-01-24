"""
FCC API Integration Module
===========================
Handles FCC database queries for station information.
"""

import requests
from tkinter import messagebox


class FCCAPIHandler:
    """Handles FCC API queries with scraper fallback"""

    # FCC API endpoints - trying data.fcc.gov first, fallback to publicfiles
    FM_API_URL = "https://data.fcc.gov/resource/4rw4-7xhp.json"
    AM_API_URL = "https://data.fcc.gov/resource/539i-7zgn.json"
    TV_API_URL = "https://data.fcc.gov/resource/4f3wj-qx5j.json"

    # Fallback endpoints
    FM_FALLBACK_URL = "https://publicfiles.fcc.gov/api/service/fm/facility/search.json"
    AM_FALLBACK_URL = "https://publicfiles.fcc.gov/api/service/am/facility/search.json"
    TV_FALLBACK_URL = "https://publicfiles.fcc.gov/api/service/tv/facility/search.json"

    def __init__(self):
        """Initialize FCC API handler"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Cellfire RF Studio - RF Planning Software'
        })
        self.scraper = None  # Lazy-load scraper only when needed

    def search_by_coordinates_and_frequency(self, lat, lon, frequency, service='FM', radius_km=10):
        """Search FCC database by coordinates and frequency

        Args:
            lat: Latitude
            lon: Longitude
            frequency: Frequency in MHz
            service: Service type ('FM', 'AM', 'TV')
            radius_km: Search radius in kilometers

        Returns:
            List of matching facilities or None
        """
        print(f"FCC API: search_by_coordinates_and_frequency called with lat={lat}, lon={lon}, freq={frequency}, service={service}, radius={radius_km}")
        try:
            # Determine API endpoint based on service
            if service.upper() == 'FM':
                api_url = self.FM_API_URL
                fallback_url = self.FM_FALLBACK_URL
                print("FCC API: Using FM data.fcc.gov endpoint")
            elif service.upper() == 'AM':
                api_url = self.AM_API_URL
                fallback_url = self.AM_FALLBACK_URL
                print("FCC API: Using AM data.fcc.gov endpoint")
            elif service.upper() == 'TV':
                api_url = self.TV_API_URL
                fallback_url = self.TV_FALLBACK_URL
                print("FCC API: Using TV data.fcc.gov endpoint")
            else:
                print("FCC API: Invalid service type")
                return None

            # Use the publicfiles API (original working endpoint)
            api_url = fallback_url
            params = {
                'latitude': lat,
                'longitude': lon,
                'searchRadius': radius_km,
            }
            if service.upper() in ['FM', 'AM']:
                params['frequency'] = frequency

            print(f"FCC API: Using API: {api_url}")
            print(f"FCC API: Parameters: {params}")

            response = self.session.get(api_url, params=params, timeout=15)
            print(f"FCC API: HTTP status: {response.status_code}")
            print(f"FCC API: Final URL: {response.url}")

            response.raise_for_status()

            data = response.json()
            print(f"FCC API: Response type: {type(data)}")
            print(f"FCC API: Response keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

            # Publicfiles API returns nested structure
            if isinstance(data, dict) and 'results' in data and 'facilities' in data['results']:
                facilities = data['results']['facilities']
                print(f"FCC API: Processing {len(facilities)} facilities from publicfiles.fcc.gov")

                # Filter by exact frequency match if provided
                if frequency:
                    facilities = [f for f in facilities
                                if abs(float(f.get('frequency', 0)) - frequency) < 0.1]

                # The publicfiles API already returns data in the expected format
                print(f"FCC API: Returning {len(facilities)} facilities")
                return facilities

            print("FCC API: Unexpected response format, returning empty")
            return []

        except requests.exceptions.RequestException as e:
            print(f"FCC API: RequestException - {e}")
            messagebox.showerror("FCC API Error",
                               f"Failed to query FCC database:\n{str(e)}")
            return None
        except Exception as e:
            print(f"FCC API: Unexpected exception - {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("FCC API Error",
                               f"Error processing FCC data:\n{str(e)}")
            return None

    def get_facility_details(self, facility_id, service='FM'):
        """Get detailed information for a specific facility

        Args:
            facility_id: FCC facility ID
            service: Service type ('FM', 'AM', 'TV')

        Returns:
            Facility details dictionary or None
        """
        try:
            # Construct API URL for facility details
            base_url = f"https://publicfiles.fcc.gov/api/service/{service.lower()}/facility/id/{facility_id}.json"

            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'facility' in data:
                return data['facility']

            return None

        except requests.exceptions.RequestException as e:
            messagebox.showerror("FCC API Error",
                               f"Failed to get facility details:\n{str(e)}")
            return None

    def format_facility_info(self, facility):
        """Format facility information for display

        Args:
            facility: Facility dictionary from FCC API

        Returns:
            Formatted string
        """
        if not facility:
            return "No facility information available"

        info = []
        info.append(f"Call Sign: {facility.get('callSign', 'N/A')}")
        info.append(f"Facility ID: {facility.get('facilityId', 'N/A')}")
        info.append(f"Service: {facility.get('service', 'N/A')}")
        info.append(f"Frequency: {facility.get('frequency', 'N/A')} MHz")
        info.append(f"City: {facility.get('city', 'N/A')}")
        info.append(f"State: {facility.get('state', 'N/A')}")
        info.append(f"Licensee: {facility.get('licensee', 'N/A')}")

        # Technical parameters
        if 'erp' in facility:
            info.append(f"ERP: {facility.get('erp', 'N/A')} kW")
        if 'haat' in facility:
            info.append(f"HAAT: {facility.get('haat', 'N/A')} meters")
        if 'antenna' in facility:
            info.append(f"Antenna: {facility.get('antenna', 'N/A')}")

        # Location
        if 'latitude' in facility and 'longitude' in facility:
            info.append(f"Location: {facility.get('latitude')}, {facility.get('longitude')}")

        return "\n".join(info)

    def search_by_call_sign_scraper(self, call_sign):
        """Search FCC database by call sign using web scraper

        Args:
            call_sign: Station call sign (e.g., "KDPI")

        Returns:
            Dictionary with scraped FCC data or None
        """
        try:
            # Lazy-load scraper
            if not self.scraper:
                from controllers.fcc_scraper import FCCScraper
                self.scraper = FCCScraper()

            print(f"FCC Scraper: Searching for call sign {call_sign}")
            results = self.scraper.search_by_call_sign(call_sign)

            if results:
                print(f"FCC Scraper: Successfully retrieved data for {call_sign}")
                return [results]  # Return as list for consistency with API
            else:
                print(f"FCC Scraper: No results for {call_sign}")
                return []

        except Exception as e:
            print(f"FCC Scraper: Error - {e}")
            messagebox.showerror("FCC Scraper Error",
                               f"Failed to scrape FCC data:\n{str(e)}\n\n"
                               "Make sure Chrome is installed.")
            return None

    def search_by_coordinates_scraper(self, lat, lon, radius_km=10, state=None):
        """Search FCC database by coordinates using web scraper

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            radius_km: Search radius in kilometers
            state: Optional state code (e.g., 'CO')

        Returns:
            List of dictionaries with scraped FCC data or None
        """
        try:
            # Lazy-load scraper
            if not self.scraper:
                from controllers.fcc_scraper import FCCScraper
                self.scraper = FCCScraper()

            print(f"FCC Scraper: Searching by coordinates {lat}, {lon}, radius={radius_km}km, state={state}")
            results = self.scraper.search_by_coordinates(lat, lon, radius_km, state)

            if results:
                print(f"FCC Scraper: Successfully retrieved {len(results)} stations")
                return results
            else:
                print("FCC Scraper: No results for coordinates")
                return []

        except Exception as e:
            print(f"FCC Scraper: Error - {e}")
            messagebox.showerror("FCC Scraper Error",
                               f"Failed to scrape FCC data:\\n{str(e)}\\n\\n"
                               "Make sure Chrome is installed.")
            return None

    def cleanup_scraper(self):
        """Cleanup scraper resources"""
        if self.scraper:
            try:
                self.scraper.stop_browser()
            except:
                pass

    def get_application_history(self, facility_id, service='FM'):
        """Get application history for a facility

        Args:
            facility_id: FCC facility ID
            service: Service type

        Returns:
            List of applications or None
        """
        try:
            base_url = f"https://publicfiles.fcc.gov/api/service/{service.lower()}/facility/id/{facility_id}/applications.json"

            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'applications' in data:
                return data['applications']

            return []

        except Exception as e:
            print(f"Error getting application history: {e}")
            return None
