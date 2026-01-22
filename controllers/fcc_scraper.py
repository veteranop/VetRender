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
