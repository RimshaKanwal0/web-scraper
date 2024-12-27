import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
)
import functools
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

# Retry decorator to handle transient exceptions
def retry(ExceptionToCheck, tries=3, delay=2, backoff=2):
    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    logging.warning(f"Exception encountered: {e}. Retrying in {mdelay} seconds...")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry

# Setup Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--start-maximized")  # Maximize browser window
chrome_options.add_argument("--disable-notifications")  # Disable pop-ups
# Uncomment the next line to run in headless mode
# chrome_options.add_argument("--headless")

# Initialize WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # URL and output file
    main_url = "https://www.grants.gov/search-grants"
    output_file = "data_7.csv"
    start_page = 7  # Specify the desired starting page number
    all_data = []
    headers_set = set([  # Known headers
        "Opportunity Number", "Opportunity Title", "Agency",
        "Opportunity Status", "Posted Date", "Close Date"
    ])

    driver.get(main_url)
    logging.info(f"Navigated to {main_url}")
    wait = WebDriverWait(driver, 20)

    # Function to go to the specified page number
    def go_to_page(target_page):
        current_page = 1
        while current_page < target_page:
            try:
                # Locate the page number button using the provided structure
                page_button = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//a[contains(@title, 'Page {current_page + 1} of')]")
                    )
                )
                page_button.click()
                current_page += 1
                logging.info(f"Navigated to page {current_page}.")
                # Wait for the table to load
                wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//table[contains(@class, 'usa-table')]//tbody/tr")
                    )
                )
                # Randomized delay to mimic human behavior
                time.sleep(random.uniform(1, 3))
            except (NoSuchElementException, TimeoutException) as e:
                logging.error(f"Failed to navigate to page {current_page + 1}: {e}")
                return False
        return True

    if start_page > 1:
        if not go_to_page(start_page):
            logging.error(f"Unable to navigate to start page {start_page}. Exiting.")
            driver.quit()
            exit()

    logging.info(f"Ready to scrape from page {start_page}.")

    # Function to scrape current page data
    def scrape_current_page(page_number):
        page_data = []
        try:
            rows = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//table[contains(@class, 'usa-table')]//tbody/tr")
                )
            )
            links = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 6:
                    continue
                try:
                    link_element = cols[0].find_element(By.TAG_NAME, "a")
                    opportunity_number = link_element.text.strip()
                    details_link = link_element.get_attribute("href").strip()
                    row_data = {
                        "Opportunity Number": opportunity_number,
                        "Opportunity Title": cols[1].text.strip(),
                        "Agency": cols[2].text.strip(),
                        "Opportunity Status": cols[3].text.strip(),
                        "Posted Date": cols[4].text.strip(),
                        "Close Date": cols[5].text.strip(),
                    }
                    links.append((row_data, details_link))
                except NoSuchElementException:
                    logging.warning("No link found in the first column.")
                    continue

            logging.info(f"Found {len(links)} opportunities on page {page_number}.")

            for idx, (row_data, details_link) in enumerate(links, start=1):
                try:
                    logging.info(f"Processing link {idx} on page {page_number}: {details_link}")
                    # Open the details link in a new tab
                    driver.execute_script("window.open(arguments[0]);", details_link)
                    driver.switch_to.window(driver.window_handles[1])  # Switch to the new tab

                    # Wait for the details page to load
                    wait.until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class='flex-6']"))
                    )
                    # Randomized delay to mimic human behavior
                    time.sleep(random.uniform(1, 2))

                    # Scrape details page information
                    try:
                        general_info_div = driver.find_element(By.XPATH, "//div[@class='flex-6']")
                        general_info_table = general_info_div.find_element(By.XPATH, ".//table")
                        rows_info = general_info_table.find_elements(By.XPATH, ".//tr")
                        for row_info in rows_info:
                            cells = row_info.find_elements(By.XPATH, ".//td")
                            if len(cells) == 2:
                                header = cells[0].text.strip().replace(":", "")
                                value = cells[1].text.strip()
                                headers_set.add(header)
                                row_data[header] = value
                    except NoSuchElementException:
                        logging.warning(f"General information section not found for Opportunity Number {row_data['Opportunity Number']}.")

                    try:
                        eligibility_div = driver.find_element(
                            By.XPATH, "//div[contains(@class, 'border-base-light')]"
                        )
                        tables = eligibility_div.find_elements(By.XPATH, ".//table")
                        for table in tables:
                            rows_elig = table.find_elements(By.XPATH, ".//tr")
                            for row_elig in rows_elig:
                                cells = row_elig.find_elements(By.XPATH, ".//td")
                                if len(cells) == 2:
                                    header = cells[0].text.strip().replace(":", "")
                                    value = cells[1].text.strip()
                                    headers_set.add(header)
                                    row_data[header] = value
                    except NoSuchElementException:
                        logging.warning(f"Eligibility section not found for Opportunity Number {row_data['Opportunity Number']}.")

                    page_data.append(row_data)

                except Exception as e:
                    logging.error(f"Error processing link {idx} on page {page_number}: {e}")
                finally:
                    # Close the details tab and switch back to the main tab
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    # Randomized delay to mimic human behavior
                    time.sleep(random.uniform(0.5, 1.5))

            write_to_csv(page_data, page_number == start_page, page_number)
        except Exception as e:
            logging.error(f"Error while scraping current page {page_number}: {e}")

    # Write data to CSV
    def write_to_csv(data, is_first_page, page_number):
        mode = "w" if is_first_page else "a"
        fieldnames = [
            "Opportunity Number", "Opportunity Title", "Agency",
            "Opportunity Status", "Posted Date", "Close Date"
        ] + sorted(list(headers_set - {
            "Opportunity Number", "Opportunity Title", "Agency",
            "Opportunity Status", "Posted Date", "Close Date"
        }))
        try:
            with open(output_file, mode, newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                if is_first_page:
                    writer.writeheader()
                for row in data:
                    complete_row = {field: row.get(field, "") for field in fieldnames}
                    writer.writerow(complete_row)
            logging.info(f"Data from page {page_number} written to {output_file}.")
        except Exception as e:
            logging.error(f"Failed to write data to CSV for page {page_number}: {e}")

    # Function to find and click the "Next" button
    def click_next_page(current_page):
        try:
            # Locate the "NEXT" button's <span> and then its parent <a>
            next_button_span = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[text()='NEXT']")
                )
            )
            next_button = next_button_span.find_element(By.XPATH, "./parent::a")
            
            # Check if the "Next" button is disabled by inspecting its class attribute
            if 'disabled' in next_button.get_attribute('class').lower():
                logging.info("Next button is disabled. Reached the last page.")
                return False
            else:
                # Click the "Next" button
                driver.execute_script("arguments[0].click();", next_button)
                logging.info(f"Clicked 'Next' to navigate to page {current_page + 1}.")
                # Wait for the new page to load
                wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//table[contains(@class, 'usa-table')]//tbody/tr")
                    )
                )
                # Randomized delay to mimic human behavior
                time.sleep(random.uniform(1, 3))
                return True
        except (NoSuchElementException, TimeoutException) as e:
            logging.info(f"No 'Next' button found or unable to click: {e}. Assuming last page reached.")
            return False
        except Exception as e:
            logging.error(f"Unexpected error when trying to click 'Next' button: {e}")
            return False

    # Main scraping loop
    current_page = start_page
    while True:
        logging.info(f"Scraping page {current_page}...")
        scrape_current_page(current_page)

        # Attempt to navigate to the next page
        has_next = click_next_page(current_page)
        if not has_next:
            logging.info("No more pages to scrape. Exiting.")
            break
        current_page += 1

    logging.info(f"Scraping completed. Data saved to {output_file}.")

finally:
    driver.quit()
    logging.info("WebDriver closed.")
