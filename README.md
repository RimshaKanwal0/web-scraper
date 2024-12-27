# web-scraper
# Web Scraper for Grants.gov Opportunities

This project is a Python-based web scraper that collects data from the [Grants.gov](https://www.grants.gov/search-grants) website. The scraper navigates through multiple pages of grant opportunities, extracts detailed information about each opportunity, and saves the data into a CSV file. It uses Selenium for web automation and incorporates robust error handling and logging mechanisms.

## Features

- **Scraping grant opportunities:** Extracts key details such as Opportunity Number, Title, Agency, Status, Posted Date, and Close Date.
- **Detailed data extraction:** Collects additional information from opportunity detail pages.
- **Paginated scraping:** Automatically navigates through multiple pages.
- **Error handling:** Implements retry logic to handle transient exceptions and recover gracefully.
- **Logging:** Provides detailed logs for each step of the scraping process.
- **Customizable:** Allows starting the scrape from any specified page.

## Installation

### Prerequisites

- Python 3.7 or higher
- Google Chrome browser
- ChromeDriver (managed automatically using `webdriver-manager`)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/grants-scraper.git
   cd grants-scraper
2. Create and activate a virtual environment (optional but recommended):
   python -m venv env
   source env/bin/activate  
3. Install the required dependencies:
   pip install -r requirements.txt
**Usage**
1. Open the scraper.py file and customize the following variables if needed:
main_url: The URL to start scraping.
output_file: The name of the CSV file to save the data.
start_page: The page number to start scraping from.
2. Run the script:
python scraper.py
3. Monitor the logs for progress and errors:
  Logs are saved in scraper.log.
**CSV Output**
The scraper saves the extracted data in a CSV file with the following default columns:
-Opportunity Number
-Opportunity Title
-Agency
-Opportunity Status
-Posted Date
-Close Date
Additional columns are dynamically added based on the details available on the detail pages.
**Dependencies**
selenium: For browser automation.
webdriver-manager: For managing ChromeDriver.
csv: For saving scraped data to a CSV file.
logging: For logging errors and progress.
functools: For retry logic.
*Install all dependencies using the command:
   pip install -r requirements.txt
**Notes**
The scraper uses randomized delays to mimic human behavior and avoid potential blocking.
It is recommended to review the terms of service for the target website to ensure compliance with their policies.

