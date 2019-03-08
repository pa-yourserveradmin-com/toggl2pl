#!/usr/bin/env python3

from tabulate import tabulate
import datetime
import requests


API_TOKEN = ''
WORKSPACE = 'rnd-y'
WORKSPACE_ID = None

AUTH = (API_TOKEN, 'api_token')

REPORTS_API_VERSION = 2
TOGGL_API_VERSION = 8

BASE_URL = 'https://toggl.com'
BASE_REPORTS_URL = '{}/reports/api/v{}'.format(BASE_URL, REPORTS_API_VERSION)
BASE_TOGGL_URL = '{}/api/v{}'.format(BASE_URL, TOGGL_API_VERSION)

SINCE = UNTIL = datetime.datetime.utcnow().isoformat()

# Table format was selected on ability to use awk with a minimal overhead. Usable formats are: plain, simple and rst.
TABLE_FORMAT = 'simple'

if not WORKSPACE_ID:
    response = requests.get(
        auth=AUTH,
        url='{}/workspaces'.format(BASE_TOGGL_URL)
    )
    for workspace in response.json():
        if workspace['name'] == WORKSPACE:
            WORKSPACE_ID = workspace['id']
            break

response = requests.get(
    auth=AUTH,
    url='{}/details?workspace_id={}&since={}&user_agent=api_test'.format(
        BASE_REPORTS_URL, WORKSPACE_ID, SINCE
    )
)

tasks = dict()
for task in response.json()['data']:
    if task['client'] not in tasks:
        tasks.update(
            {
                task['client']: {
                    task['project']: {
                        task['description']: int(task['dur'] / 1000)
                    }
                }
            }
        )
        continue
    if task['project'] not in tasks[task['client']]:
        tasks[task['client']]['project'] = {
            task['description']: int(task['dur'] / 1000)
        }
        continue
    if task['description'] not in tasks[task['client']][task['project']]:
        tasks[task['client']][task['project']].update(
            {
                task['description']: int(task['dur'] / 1000)
            }
        )
        continue
    tasks[task['client']][task['project']][task['description']] += int(task['dur'] / 1000)

rows = list()
headers = ('Client', 'Project', 'Description', 'Duration (sec)')
for client, projects in sorted(tasks.items()):
    for project, data in sorted(projects.items()):
        for description, duration in sorted(data.items()):
            rows.append([client, project, description, duration])

print(tabulate(tabular_data=rows, headers=headers, tablefmt=TABLE_FORMAT))
