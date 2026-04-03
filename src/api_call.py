import requests
import os
import json

data = {
    'action': 'get_page_data_calendar',
    'auto_callback': 'get_page_data_calendar',
    'form_submit_callback': 'get_page_data_calendar',
    'cal_month': '3',
    'cal_year': '2026',
    'location_id': '1',
}

if os.path.exists("session.json"):
    session = json.load(open("session.json"))
    cookies = session["cookies"][0]
    headers = session["headers"][0]
else:
    raise FileNotFoundError("session.json not found.")

response = requests.post('https://stevensems.com/cq/lib/php/cq_functions.php', cookies=cookies, headers=headers, data=data)

if response.status_code == 200:
    # print("Request successful!")
    if not os.path.exists("target"):
        os.makedirs("target")
    file_path = os.path.join(os.getcwd(), './target/response.json')
    with open(file_path, 'w') as f:
        json.dump(response.json()["data"]["calendar"]["1"], f, indent=2)
else:
    raise Exception("Failed to fetch calendar data." + f"Status code: {response.status_code}")