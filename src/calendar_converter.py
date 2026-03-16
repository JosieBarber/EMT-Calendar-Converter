from webscraper import scrape_schedule, fetch_html_content
from calendar_events import create_event, get_calendar_service, verify_calendar_exists
from datetime import datetime
import getpass

name = input("Enter your first name (capitalized first letter): ")
username = input("Enter your Crew Quarters username: ")
password = getpass.getpass("Enter your password (input hidden): ")

month = input("Enter the month to scrape (1-12, default current month): ")
if month:
    month = int(month)
else:
    month = datetime.now().month

year = input("Enter the year to scrape (e.g., 2024, default current year): ")

if year:
    year = int(year)
else:
    year = datetime.now().year

# print("Scraping schedule for {name} for month {month}/{year}".format(name = name, month = month, year = year))
shifts = scrape_schedule(username, password, name, month, year)
print("Schedule scraping completed successfully. \n\n")

calendar_name = input("Enter the wanted calendar name: ")

service = get_calendar_service()
calendar_id = verify_calendar_exists(service, calendar_name)

for shift in shifts:
    create_event(service, calendar_id, shift["date"], shift["time"], shift["shift"])
