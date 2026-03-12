import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def format_event(date, time, shift):
    if time == "AM":
        start_time = datetime.datetime.combine(date, datetime.time(7, 0))
        end_time = datetime.datetime.combine(date, datetime.time(19, 0))
    elif time == "PM":
        start_time = datetime.datetime.combine(date, datetime.time(19, 0))
        end_time = datetime.datetime.combine(date + datetime.timedelta(days=1), datetime.time(7, 0))
    else:
        raise ValueError("Invalid time value. Must be 'AM' or 'PM'.")

    if shift == "First":
        shift_type = "PRIMARY"
        color_Id = 2
    elif shift == "Second":
        shift_type = "SECONDARY"
        color_Id = 5
    elif shift == "Third":
        shift_type = "THIRD OUT"
        color_Id = 6

    event = {
      "summary": f"{shift_type}",
      "colorId": color_Id,
      "start": {
        "dateTime": start_time.isoformat(),
        "timeZone": "America/Chicago",
      },
      "end": {
        "dateTime": end_time.isoformat(),
        "timeZone": "America/Chicago",
      },
    }

    return event

def create_event(service, calendar_id, date, time, shift):
    """
    Create an event in the specified calendar.

    @param service: Google Calendar API service instance
    @param calendar_id: ID of the calendar where the event will be created
    @param date: Date of the event
    @param time: Time slot of the event ("AM" or "PM")
    @param shift: Shift type of the event ("First", "Second", or "Third")
    """

    event = format_event(date, time, shift)
    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    print('Event created: %s' % (created_event.get('htmlLink')))

def get_calendar_service():
  """
    Get a Google Calendar API service instance.

    @return: Google Calendar API service instance
  """

  creds = None
  if os.path.exists("token.json"):
      creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
      else:
          flow = InstalledAppFlow.from_client_secrets_file(
              "credentials.json", SCOPES
          )
          creds = flow.run_local_server(port=0)
      with open("token.json", "w") as token:
          token.write(creds.to_json())

  service = build("calendar", "v3", credentials=creds)
  return service

def verify_calendar_exists(service, calendar_name):
    """
    Ensure a calendar with the given name exists.

    @param service: Google Calendar API service instance
    @param calendar_name: Name of the calendar to verify
    @return: Calendar ID if exists, None otherwise
    """
    calendar_list = service.calendarList().list().execute()
    calendar_id = None

    # Look for existing "EMT" calendar
    for calendar in calendar_list["items"]:
        if calendar["summary"] == calendar_name:
            calendar_id = calendar["id"]
            break

    # If not found, create it
    if calendar_id is None:
        new_calendar = {
            "summary": calendar_name,
            "timeZone": "America/Chicago"
        }

        created_calendar = service.calendars().insert(body=new_calendar).execute()
        calendar_id = created_calendar["id"]
        print("Created calendar:", calendar_id)
    else:
        print("Found calendar:", calendar_id)
    return calendar_id


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.app.created", "https://www.googleapis.com/auth/calendar.calendarlist.readonly"]


def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  try:
    service = get_calendar_service()
    emt_calendar_id = verify_calendar_exists(service, "EMT-TEMP")
    create_event(service, emt_calendar_id, datetime.date(2026, 3, 13), "PM", "Third")
  except HttpError as error:
    print("An error occurred: %s" % error)
main()s