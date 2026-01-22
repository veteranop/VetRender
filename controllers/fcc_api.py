"""
FCC API Integration Module
===========================
Handles FCC database queries for station information.
"""

import requests
from tkinter import messagebox


class FCCAPIHandler:
    """Handles FCC API queries"""

    # FCC API endpoints
    FM_API_URL = "https://publicfiles.fcc.gov/api/service/fm/facility/search.json"
    AM_API_URL = "https://publicfiles.fcc.gov/api/service/am/facility/search.json"
    TV_API_URL = "https://publicfiles.fcc.gov/api/service/tv/facility/search.json"

    def __init__(self):
        """Initialize FCC API handler"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VetRender RF Planning Software'
        })

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
        try:
            # Determine API endpoint based on service
            if service.upper() == 'FM':
                api_url = self.FM_API_URL
            elif service.upper() == 'AM':
                api_url = self.AM_API_URL
            elif service.upper() == 'TV':
                api_url = self.TV_API_URL
            else:
                return None

            # Build query parameters
            params = {
                'latitude': lat,
                'longitude': lon,
                'radius': radius_km,
            }

            # Add frequency to params if it's FM/AM
            if service.upper() in ['FM', 'AM']:
                params['frequency'] = frequency

            # Make API request
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Parse results
            if 'results' in data and 'facilities' in data['results']:
                facilities = data['results']['facilities']

                # Filter by exact frequency match if provided
                if frequency:
                    facilities = [f for f in facilities
                                if abs(float(f.get('frequency', 0)) - frequency) < 0.1]

                return facilities

            return []

        except requests.exceptions.RequestException as e:
            messagebox.showerror("FCC API Error",
                               f"Failed to query FCC database:\n{str(e)}")
            return None
        except Exception as e:
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
