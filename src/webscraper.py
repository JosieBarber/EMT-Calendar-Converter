from bs4 import BeautifulSoup
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def fetch_html_content(username, password):
    """
    Uses Selenium to log in and fetch the fully rendered HTML of the calendar page.

    @param username: Crew Quarters username
    @param password: Crew Quarters password
    @return: HTML content of the schedule page as a string
    """
    login_url = "https://stevensems.com/cq/index.php?v=login_form&iframe=true"
    calendar_url = "https://stevensems.com/cq/index.php?p=calendar"

    # Setup Chrome headless (runs in background)
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open login page
        driver.get(login_url)
        time.sleep(1)

        # Enter credentials and submit form
        driver.find_element(By.ID, "sign_in_username").send_keys(username)
        driver.find_element(By.ID, "sign_in_password").send_keys(password)
        driver.find_element(By.ID, "sign_in_button").click()

        # Wait for login to be complete
        driver.switch_to.default_content()
        time.sleep(1)

        # Open calendar page
        driver.get(calendar_url)
        time.sleep(1)

        # Get and return html content of the page
        html_content = driver.page_source
        return html_content

    finally:
        # Prevent real crashes if things go sideways
        # Close the browser after fetching the content
        driver.quit()


def extract_shift_details(shift_element):
    """
    Extract shift details from a shift HTML snippet.

    @param shift_element: HTML snippet of a single shift (as string)
    @return: Dictionary with shift details (date, time, shift type, employee name)
    """
    
    soup = BeautifulSoup(shift_element, "html.parser")

    td = soup.find("td")
    if not td or "id" not in td.attrs:
        return None # Should replace with an exception or error
    
    shift_id = td["id"]
    parts = shift_id.split("_")

    date_part = parts[2]
    shift_number = int(parts[3])
    date_obj = datetime.strptime(date_part, "%Y-%m-%d")
    

    # Determine time and shift type based on shift number
    if 1 <= shift_number <= 3:
        time, shift_type = "AM", "First"
    elif 4 <= shift_number <= 6:
        time, shift_type = "PM", "First"
    elif 7 <= shift_number <= 9:
        time, shift_type = "AM", "Second"
    elif 10 <= shift_number <= 12:
        time, shift_type = "PM", "Second"
    elif 13 <= shift_number <= 15:
        time, shift_type = "AM", "Third"
    elif 16 <= shift_number <= 18:
        time, shift_type = "PM", "Third"
    else:
        time, shift_type = "Unknown", "Unknown"
    
    link = soup.find("a", class_="cal_shift")
    name = "Unknown"
    
    # Extract the name from the title attribute of the link
    if link and "title" in link.attrs:
        title = link["title"]
        match = re.search(r'(?:EMT|MEDIC|Crew):\s*([A-Za-z]+)', title)
        if match:
            name = match.group(1)

    # Return the extracted details as a dictionary
    return {
        "date": date_obj,
        "time": time,
        "shift": shift_type,
        "name": name
    }

def extract_all_shifts(html_page):
    """
    Parse an entire HTML page as a string and extract all shift entries.

    @param html_page: HTML content of the schedule page
    @return: List of dictionaries containing shift details
    """

    soup = BeautifulSoup(html_page, "html.parser")
    shifts = []

    # Find all td elements whose id matches the shift pattern
    shift_cells = soup.find_all("td", id=re.compile(r"^shift_\d+_\d{4}-\d{2}-\d{2}_\d+$"))

    for cell in shift_cells:
        shift_html = str(cell)
        shift_data = extract_shift_details(shift_html)

        if shift_data and all(value != "Unknown" for value in shift_data.values()) and len(shift_data["name"]) >= 2:
            shifts.append(shift_data)

    return shifts

# TODO: Main scraping function to orchestrate the entire workflow
def scrape_schedule(username, password, name):
    """
    Main function to scrape the schedule for a specific user.

    @param username: Crew Quarters username
    @param password: Crew Quarters password
    @param name: First name of the user to filter shifts
    """
    html_page = str(fetch_html_content(username, password))
    shifts = extract_all_shifts(html_page)
    print(f"Extracted {len(shifts)} shifts from the schedule.")

    # Filter shifts for the specified name and print them
    for shift in shifts:
        if shift["name"] == name:
            print(shift)