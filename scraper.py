import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def scrape_fcc_facility(callsign):
    """
    Scrapes FCC ULS facility data for a given callsign.
    Returns a list of facility dicts or raises an exception.
    """
    # Set up headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Navigate to FCC ULS search
        search_url = f"https://www.fcc.gov/uls/search?call={callsign}"
        driver.get(search_url)

        # Wait for page to load (adjust if needed)
        time.sleep(3)  # Mimic human delay to avoid rate limits

        # Get page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Parse results table (adjust selectors based on FCC HTML)
        facilities = []
        results_table = soup.find('table', class_='results')  # Example class; inspect FCC page for accuracy
        if results_table:
            rows = results_table.find('tbody').find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    facilities.append({
                        'facility_id': cols[0].text.strip(),
                        'callsign': cols[1].text.strip(),
                        'location': cols[2].text.strip(),
                        'status': cols[3].text.strip(),
                    })

        driver.quit()
        return facilities
    except Exception as e:
        driver.quit()
        raise Exception(f"Failed to scrape FCC data: {str(e)}. Try manual entry or check FCC website.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <callsign>")
        sys.exit(1)

    callsign = sys.argv[1]
    try:
        results = scrape_fcc_facility(callsign)
        import json
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(str(e))