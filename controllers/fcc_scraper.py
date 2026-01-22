"""
FCC Scraper Module
==================
Scrapes FCC FM Query database using Selenium when API is unavailable.
Based on WebScraperMain.py by alethea, modified for VetRender.
"""

import os
import json
import logging
import time
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class FCCScraper:
    """Scrapes FCC FM Query website for station information"""

    FCC_FM_QUERY_URL = "https://transition.fcc.gov/fcc-bin/fmq"

    def __init__(self):
        """Initialize FCC scraper"""
        self.driver = None
        self.results_dir = os.path.join(os.getcwd(), 'results')
        os.makedirs(self.results_dir, exist_ok=True)

        # Setup logging
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            filename='logs/fcc_scraper.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    @staticmethod
    def decimal_to_dms(decimal_degrees, is_latitude=True):
        """Convert decimal degrees to degrees, minutes, seconds

        Args:
            decimal_degrees: Decimal degree value
            is_latitude: True for latitude (N/S), False for longitude (E/W)

        Returns:
            Tuple of (degrees, minutes, seconds, direction)
        """
        # Determine direction
        if is_latitude:
            direction = 'N' if decimal_degrees >= 0 else 'S'
        else:
            direction = 'E' if decimal_degrees >= 0 else 'W'

        # Work with absolute value
        abs_degrees = abs(decimal_degrees)

        # Extract degrees, minutes, seconds
        degrees = int(abs_degrees)
        minutes_decimal = (abs_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60

        return degrees, minutes, seconds, direction

    def start_browser(self):
        """Start headless Chrome browser"""
        if self.driver:
            return

        logging.info("Starting headless Chrome browser")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            # Set page load timeout to 3 minutes (FCC site can be slow)
            self.driver.set_page_load_timeout(180)
            logging.info("Browser started successfully")
        except Exception as e:
            logging.error(f"Failed to start browser: {e}")
            raise

    def stop_browser(self):
        """Stop browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logging.info("Browser stopped")

    def search_by_call_sign(self, call_sign):
        """Search FCC database by call sign

        Args:
            call_sign: Station call sign (e.g., "KDPI")

        Returns:
            Dictionary with parsed FCC data or None if failed
        """
        try:
            if not self.driver:
                self.start_browser()

            logging.info(f"Searching for call sign: {call_sign}")

            # Build search URL
            search_url = f"{self.FCC_FM_QUERY_URL}?{urllib.parse.urlencode({'call': call_sign})}"
            logging.info(f"Search URL: {search_url}")

            # Navigate to URL
            self.driver.get(search_url)

            # Wait for page to load (look for "Frequency" keyword)
            WebDriverWait(self.driver, 30).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Frequency')
            )

            # Get full page text
            full_text = self.driver.find_element(By.TAG_NAME, 'body').text

            # Parse the text into structured data
            parsed_data = self._parse_fcc_text(full_text, call_sign)

            logging.info(f"Successfully scraped data for {call_sign}")
            return parsed_data

        except Exception as e:
            logging.error(f"Error scraping {call_sign}: {e}")
            return None

    def search_by_coordinates(self, lat, lon, radius_km=10, state=None):
        """Search FCC database by coordinates

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            radius_km: Search radius in kilometers (default 10)
            state: Optional state code (e.g., 'CO')

        Returns:
            List of dictionaries with parsed FCC data or None if failed
        """
        try:
            if not self.driver:
                self.start_browser()

            logging.info(f"Searching by coordinates: {lat}, {lon}, radius={radius_km}km, state={state}")

            # Convert decimal degrees to DMS
            lat_d, lat_m, lat_s, lat_dir = self.decimal_to_dms(lat, is_latitude=True)
            lon_d, lon_m, lon_s, lon_dir = self.decimal_to_dms(lon, is_latitude=False)

            logging.info(f"Converted to DMS: {lat_d}°{lat_m}'{lat_s:.1f}\"{lat_dir}, {lon_d}°{lon_m}'{lon_s:.1f}\"{lon_dir}")

            # Build URL parameters (FCC accepts direct URL params)
            # Based on working FCC form, include all standard fields
            params = {
                'call': '',          # Empty for coordinate search
                'filenumber': '',
                'state': state if state else '',
                'city': '',
                'freq': '',          # Empty for all frequencies
                'fre2': '',
                'single': '0',       # 0 = show all, 1 = single frequency
                'serv': '',
                'status': '',
                'facid': '',
                'asrn': '',
                'class': '',
                'list': '0',         # 0 = results to page
                'ThisTab': 'Results to This Page/Tab',
                'dist': radius_km,
                'dlat2': lat_d,
                'mlat2': lat_m,
                'slat2': f'{lat_s:.0f}',
                'NS': lat_dir,
                'dlon2': lon_d,
                'mlon2': lon_m,
                'slon2': f'{lon_s:.0f}',
                'EW': lon_dir,
                'size': '9'
            }

            # Build search URL
            search_url = f"{self.FCC_FM_QUERY_URL}?{urllib.parse.urlencode(params)}"
            logging.info(f"Search URL: {search_url}")

            # For coordinate searches, the FCC returns JavaScript variables, not HTML
            # We can use requests directly instead of Selenium for better performance
            import requests

            try:
                response = requests.get(search_url, timeout=30)
                response.raise_for_status()
                page_text = response.text
                logging.info(f"Fetched page successfully ({len(page_text)} bytes)")
            except Exception as e:
                logging.error(f"Direct request failed: {e}, falling back to Selenium")
                # Fallback to Selenium if direct request fails
                self.driver.get(search_url)
                WebDriverWait(self.driver, 60).until(
                    lambda driver: len(driver.find_element(By.TAG_NAME, 'body').text) > 10
                )
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text

            # Debug: Save the raw response
            debug_file = os.path.join(self.results_dir, f'debug_coords_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"Coordinates: {lat}, {lon}\n")
                f.write(f"DMS: {lat_d}°{lat_m}'{lat_s:.2f}\"{lat_dir}, {lon_d}°{lon_m}'{lon_s:.2f}\"{lon_dir}\n")
                f.write(f"Radius: {radius_km} km, State: {state}\n")
                f.write("="*80 + "\n")
                f.write(page_text)
            logging.info(f"Debug: Saved page response to {debug_file}")

            # Try to parse JavaScript variable format first (FCC returns this for coordinate searches)
            if '=' in page_text and ';' in page_text:
                logging.info("Detected JavaScript variable format, parsing...")
                results = self._parse_javascript_vars(page_text)
            else:
                # Fall back to text parsing
                logging.info("Using text parsing")
                results = self._parse_multi_station_text(page_text)

            logging.info(f"Successfully scraped {len(results)} stations")
            return results

        except Exception as e:
            logging.error(f"Error scraping by coordinates: {e}")
            return None

    def _parse_fcc_text(self, text, call_sign):
        """Parse FCC query result text into structured data

        Args:
            text: Full page text from FCC query
            call_sign: Call sign being searched

        Returns:
            Dictionary with parsed fields
        """
        data = {
            'callSign': call_sign,
            'full_license_info': text,
            'query_time': datetime.now().isoformat(),
            'source': 'FCC FM Query (Scraped)'
        }

        # Parse key fields from text
        lines = text.split('\n')

        for line in lines:
            line = line.strip()

            # Try to extract common fields
            if 'Frequency:' in line:
                try:
                    freq = line.split('Frequency:')[1].strip().split()[0]
                    data['frequency'] = freq
                except:
                    pass

            elif 'City:' in line:
                try:
                    city = line.split('City:')[1].strip()
                    data['city'] = city
                except:
                    pass

            elif 'State:' in line:
                try:
                    state = line.split('State:')[1].strip().split()[0]
                    data['state'] = state
                except:
                    pass

            elif 'Facility ID:' in line or 'FacilityID:' in line:
                try:
                    fac_id = line.split(':')[1].strip().split()[0]
                    data['facilityId'] = fac_id
                except:
                    pass

            elif 'Licensee:' in line:
                try:
                    licensee = line.split('Licensee:')[1].strip()
                    data['licensee'] = licensee
                except:
                    pass

            elif 'Latitude:' in line:
                try:
                    lat_str = line.split('Latitude:')[1].strip().split()[0]
                    data['latitude'] = lat_str
                except:
                    pass

            elif 'Longitude:' in line:
                try:
                    lon_str = line.split('Longitude:')[1].strip().split()[0]
                    data['longitude'] = lon_str
                except:
                    pass

            elif 'ERP:' in line or 'Effective Radiated Power' in line:
                try:
                    erp_str = line.split(':')[1].strip().split()[0]
                    data['erp'] = erp_str
                except:
                    pass

            elif 'HAAT:' in line or 'Height Above Average Terrain' in line:
                try:
                    haat_str = line.split(':')[1].strip().split()[0]
                    data['haat'] = haat_str
                except:
                    pass

        return data

    def _parse_javascript_vars(self, text):
        """Parse FCC JavaScript variable format response

        The FCC returns data as JavaScript variable assignments like:
        c_callsign = 'KDPI';
        freq = '88.5';
        etc.

        Args:
            text: Page text containing JavaScript variables

        Returns:
            List of dictionaries with parsed station data
        """
        import re

        results = []

        # Extract all variable assignments
        station_data = {}

        # Match patterns like: var_name = 'value'; or var_name = value;
        pattern = r"(\w+)\s*=\s*['\"]?([^;'\"]+)['\"]?\s*;"
        matches = re.findall(pattern, text)

        for var_name, value in matches:
            value = value.strip()
            if value and value != '-':
                station_data[var_name] = value

        # Convert to our standard format if we found data
        if station_data:
            station = {
                'query_time': datetime.now().isoformat(),
                'source': 'FCC FM Query (Scraped - Coordinates)'
            }

            # Map FCC variable names to our field names
            if 'c_callsign' in station_data or 'c_facility_callsign' in station_data:
                station['callSign'] = station_data.get('c_callsign') or station_data.get('c_facility_callsign')

            if 'freq' in station_data:
                station['frequency'] = station_data['freq']

            if 'c_comm_city_app' in station_data:
                station['city'] = station_data['c_comm_city_app']

            if 'c_comm_state_app' in station_data:
                station['state'] = station_data['c_comm_state_app']

            if 'facility_id' in station_data:
                station['facilityId'] = station_data['facility_id']

            if 'c_service' in station_data:
                station['service'] = station_data['c_service']

            if 'c_station_class' in station_data:
                station['stationClass'] = station_data['c_station_class']

            # Coordinates
            if 'alat83' in station_data and 'alon83' in station_data:
                station['latitude'] = station_data['alat83']
                station['longitude'] = station_data['alon83']

            results.append(station)

        return results

    def _parse_multi_station_text(self, text):
        """Parse FCC query result text with multiple stations

        Args:
            text: Full page text from FCC query

        Returns:
            List of dictionaries with parsed station data
        """
        results = []

        # Split by station records (look for Call Sign patterns)
        lines = text.split('\n')
        current_station = None

        for line in lines:
            line = line.strip()

            # Check if this is a new station (usually starts with call sign pattern)
            if 'Call Sign:' in line or 'Callsign:' in line:
                # Save previous station if exists
                if current_station and 'callSign' in current_station:
                    results.append(current_station)

                # Start new station
                current_station = {
                    'query_time': datetime.now().isoformat(),
                    'source': 'FCC FM Query (Scraped - Coordinates)'
                }

                try:
                    call_sign = line.split(':')[1].strip().split()[0]
                    current_station['callSign'] = call_sign
                except:
                    pass

            # Parse other fields for current station
            if current_station:
                if 'Frequency:' in line:
                    try:
                        freq = line.split('Frequency:')[1].strip().split()[0]
                        current_station['frequency'] = freq
                    except:
                        pass

                elif 'City:' in line:
                    try:
                        city = line.split('City:')[1].strip()
                        current_station['city'] = city
                    except:
                        pass

                elif 'State:' in line:
                    try:
                        state = line.split('State:')[1].strip().split()[0]
                        current_station['state'] = state
                    except:
                        pass

                elif 'Facility ID:' in line or 'FacilityID:' in line:
                    try:
                        fac_id = line.split(':')[1].strip().split()[0]
                        current_station['facilityId'] = fac_id
                    except:
                        pass

        # Don't forget last station
        if current_station and 'callSign' in current_station:
            results.append(current_station)

        return results

    def save_results(self, results, call_sign):
        """Save scraping results to JSON file

        Args:
            results: Dictionary with scraped data
            call_sign: Call sign for filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fcc_{call_sign}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=4)

        logging.info(f"Results saved to {filepath}")
        return filepath


# Standalone test function
if __name__ == '__main__':
    import sys

    # Get call sign from command line or use default
    call_sign = sys.argv[1] if len(sys.argv) > 1 else 'KDPI'

    print(f"Scraping FCC data for {call_sign}...")

    scraper = FCCScraper()
    try:
        results = scraper.search_by_call_sign(call_sign)

        if results:
            print("\nResults:")
            print(json.dumps(results, indent=2))

            # Save to file
            filepath = scraper.save_results(results, call_sign)
            print(f"\nSaved to: {filepath}")
        else:
            print("No results found")

    finally:
        scraper.stop_browser()
