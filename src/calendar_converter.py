from webscraper import scrape_schedule, fetch_html_content
from calendar_events import create_event, get_calendar_service, verify_calendar_exists
import getpass
import datetime

name = input("Enter your first name (capitalized first letter): ")
username = input("Enter your Crew Quarters username: ")
password = getpass.getpass("Enter your password (input hidden): ")

scrape_schedule(username, password, name)
print("Schedule scraping completed successfully. \n\n")

calendar_name = input("Enter the wanted calendar name: ")

service = get_calendar_service()
emt_calendar_id = verify_calendar_exists(service, calendar_name)

create_event(service, emt_calendar_id, datetime.date(2026, 3, 13), "AM", "First")