import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.app.created", "https://www.googleapis.com/auth/calendar.calendarlist.readonly"]


def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # service = build("calendar", "v3", credentials=creds)
    service = build("calendar", "v3", credentials=creds)


    # Get all calendars
    calendar_list = service.calendarList().list().execute()

    emt_calendar_id = None

    # Look for existing "EMT" calendar
    for calendar in calendar_list["items"]:
        if calendar["summary"] == "Womp":
            emt_calendar_id = calendar["id"]
            break

    # If not found, create it
    if emt_calendar_id is None:
        new_calendar = {
            "summary": "Womp",
            "timeZone": "America/Chicago"
        }

        created_calendar = service.calendars().insert(body=new_calendar).execute()
        emt_calendar_id = created_calendar["id"]
        print("Created calendar:", emt_calendar_id)
    else:
        print("Found calendar:", emt_calendar_id)

  except HttpError as error:
    print(f"An error occurred: {error}")

  event = {
    'summary': 'Google I/O 2015',
    'location': '800 Howard St., San Francisco, CA 94103',
    'description': 'A chance to hear more about Google\'s developer products.',
    'start': {
      'dateTime': '2026-03-13T09:00:00-07:00',
      'timeZone': 'America/Los_Angeles',
    },
    'end': {
      'dateTime': '2026-03-13T17:00:00-07:00',
      'timeZone': 'America/Los_Angeles',
    },
    'recurrence': [
    ],
    'reminders': {
      'useDefault': False,
      'overrides': [
        {'method': 'email', 'minutes': 24 * 60},
        {'method': 'popup', 'minutes': 10},
      ],
    },
  }

  event = service.events().insert(calendarId=emt_calendar_id, body=event).execute()
  print('Event created: %s' % (event.get('htmlLink')))

main()

