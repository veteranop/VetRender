'''
Created on 8 Nov 2017

@author: alethea
Modified for VetRender: Headless Chrome, output to file, search by call sign
'''

'''
1) Import packages
'''
import json
import os
import logging
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

'''
2) Import helper functions from other python modules
'''
from tp_status import tp_status # to scrape data for companies with tp status
from lease_id import lease_id # to scrape data for companies with lease ID
from call_sign import call_sign # to scrape data for companies with call sign

'''
3) Initialize data structures
'''
data_list = []  # list of dicts for results
no_results = []  # list of call signs with no results

# create header row
headerRow = ["Subsidiary", "Call Sign/Lease ID", "Name", "FRN", "Radio Service", "Status", "Version", "Last Action Date", "Market", "Submarket", "Channel Block", "Associated Frequencies (MHz)", "Grant", "Effective", "Expiration", "Cancellation", "1st Buildout Deadline", "2nd Buildout Deadline", "Licensee ID", "Auction"]

'''
4) Initialize global variable
'''

rowTracker = 0  # to track row in data list
subTracker = ""  # to track call sign we are currently searching



def subSearch(sub):
    logging.info(f"Searching for {sub}")
    search_url = 'https://transition.fcc.gov/fcc-bin/fmq?' + urllib.parse.urlencode({'call': sub})
    logging.info(f"Search URL: {search_url}")
    driver.get(search_url)
    WebDriverWait(driver, 30).until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Frequency'))
    # Get full license information
    full_text = driver.find_element(By.TAG_NAME, 'body').text
    data = {'full_license_info': full_text}
    row_data = {'Call Sign': sub}
    row_data.update(data)
    data_list.append(row_data)
    logging.info(f"Extracted data for {sub}")

if __name__ == '__main__':
    import sys
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(filename='logs/scraper.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info("Starting FCC scraper")
    options = Options()
    options.add_argument("--headless")
    global driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Get call signs from command line arguments or default
    if len(sys.argv) > 1:
        call_signs = sys.argv[1:]
    else:
        call_signs = ['KDPI']  # Default to KDPI for testing

    for cs in call_signs:
        subSearch(cs)

    driver.quit()

    # Save results to JSON
    results_path = os.path.join('results', 'fcc_results.json')
    with open(results_path, 'w') as f:
        json.dump({'results': data_list, 'no_results': no_results}, f, indent=4)
    logging.info(f"Scraping completed. Results saved to {results_path}. Total results: {len(data_list)}, No results: {len(no_results)}")

    print("Scraping completed. Results saved to " + results_path)