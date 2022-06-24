import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import rfc3339
from datetime import datetime, timedelta

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']


def retrieve_task_data(cred_fpath: str):
    """
    :param cred_fpath: File path to `credentials.json`
    """

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_fpath, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('tasks', 'v1', credentials=creds)

        # === WHERE THE ACTUAL FUN PART STARTS ===

        # Call the Tasks API
        results = service.tasklists().list(maxResults=10).execute()
        items = results.get('items', [])

        if not items:
            print('No task lists found.')
            return

        data = {}

        for item in items:
            data[item["title"]] = []
            # tl_raw = service.tasklists().get(tasklist=item["id"]).execute()
            tasks_content = service.tasks().list(tasklist=item["id"], showCompleted=True, showHidden=True).execute()
            for task_item in tasks_content["items"]:
                if not task_item["title"].isspace():
                    overdue: bool
                    duedate: datetime = rfc3339.parse_datetime(t) if (t := task_item.get("due", None)) is not None else None
                    complete: datetime = rfc3339.parse_datetime(t) if (t := task_item.get("completed", None)) is not None else None
                    if complete is None and duedate is not None:
                        overdue = duedate < datetime.now().replace(tzinfo=rfc3339.UTC_TZ)
                    else:
                        overdue = False
                    task = (overdue, duedate, complete)
                    data[item["title"]].append(task)

        return data
    except HttpError as err:
        print(err)

"""
Data that is needed for the display:
- Get the entire tasklists
- Get all the tasks on each tasklist
-- Each task items returned must filter task-names with only whitespaces (these don't count, and comes up often b/c)
-- Each task items must then have following properties prepared
--- 1. Overdue: T/F
--- 2. Deadline Date
--- 3. Completion Date

{
"TASKLIST #1": [
    (T/F, DUE, COMPL, ),
    (T/F, DUE, COMPL, ),
    (T/F, DUE, COMPL, ),
],
"TASKLIST #2": [
    ...
],
"TASKLIST #3": [
    ...
],
}
"""


# modified: https://stackoverflow.com/a/37169435/9985581
# NOTE: on the basis that every week starts with Monday
def check_week_same(date1: datetime, date2: datetime):
    return date1.isocalendar()[1] == date2.isocalendar()[1] and date1.year == date2.year


# modified: https://stackoverflow.com/a/2119512/9985581
def timedelta_convert(td: timedelta):
    return td.days, td.seconds//3600, (td.seconds//60)%60  # days hours minutes


def process_tasks(cur_tdt: list[tuple[bool, datetime, datetime]]):
    today = datetime.today()
    print(">>", today.month, today.day, today.weekday())

    mdt = {"unfinished": 0, "soon": 0, "overdue": 0, "finished": 0,}
    wdt = {"unfinished": 0, "soon": 0, "overdue": 0, "finished": 0,}
    ddt = {"unfinished": 0, "soon": 0, "overdue": 0, "finished": 0,}

    for item in cur_tdt:
        if item[0]:
            # is overdued (if overdued, all timeframes will factor in the overdue)
            mdt["overdue"] += 1
            wdt["overdue"] += 1
            ddt["overdue"] += 1
        else:
            if item[2] is not None:  # completed
                if today.year == item[2].year and today.month == item[2].month:
                    mdt["finished"] += 1
                    if check_week_same(today, item[2]):
                        wdt["finished"] += 1
                        if today.day == item[2].day:
                            ddt["finished"] += 1
            else:  # not complete (unfinished & soon)
                if item[1] is not None:  # deadline, still unfinished & soon
                    if timedelta_convert(item[1] - today.replace(tzinfo=rfc3339.UTC_TZ))[1] <= 1:  # within an hour (daily chart)
                        ddt["soon"] += 1
                    else:
                        ddt["unfinished"] += 1

                    if timedelta_convert(item[1] - today.replace(tzinfo=rfc3339.UTC_TZ))[0] <= 1:  # within a day (weekly chart)
                        wdt["soon"] += 1
                    else:
                        wdt["unfinished"] += 1

                    if timedelta_convert(item[1] - today.replace(tzinfo=rfc3339.UTC_TZ))[0] <= 7:  # within a week (monthly chart)
                        mdt["soon"] += 1
                    else:
                        mdt["unfinished"] += 1

                else:  # no deadline (but doesn't have the completed key)
                    mdt["unfinished"] += 1
                    wdt["unfinished"] += 1
                    ddt["unfinished"] += 1

    return {
        "monthly": (today.strftime("%B"), mdt),
        "weekly": ((today-timedelta(days=today.weekday())).date().strftime("Week of %m/%d (Mon)"), wdt),
        "daily": (datetime.today().strftime("%m/%d"), ddt),
    }


if __name__ == '__main__':
    data = retrieve_task_data("credentials.json")
    print(data)
    for k in data:
        print(k)
        for l in data[k]:
            print("\t", l)
            if l[1] is not None: print(l[1])
