from webscraper import scrape_schedule, fetch_html_content
from calendar_events import create_event, get_calendar_service, verify_calendar_exists
import getpass
import datetime

name = input("Enter your first name (capitalized first letter): ")
username = input("Enter your Crew Quarters username: ")
password = getpass.getpass("Enter your password (input hidden): ")

shifts = scrape_schedule(username, password, name)
print(shifts)
print("Schedule scraping completed successfully. \n\n")

calendar_name = input("Enter the wanted calendar name: ")

service = get_calendar_service()
calendar_id = verify_calendar_exists(service, calendar_name)


for shift in shifts:
    # print(shift)
    # print("\n")
    create_event(service, calendar_id, shift["date"], shift["time"], shift["shift"])
# create_event(service, calendar_id, shifts["date"], shifts["time"], shifts["shift"])