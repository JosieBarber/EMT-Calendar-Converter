from webscraper import scrape_schedule, fetch_html_content
import getpass

name = input("Enter your first name (capitalized first letter): ")
username = input("Enter your Crew Quarters username: ")
password = getpass.getpass("Enter your password (input hidden): ")
scrape_schedule(username, password, name)