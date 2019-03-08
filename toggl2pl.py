#!/usr/bin/env python3

from datetime import datetime
from tabulate import tabulate
from toggl2pl import PL
from toggl2pl import TogglReportsClient
import sys
import textwrap
import yaml


def rounded(minutes):
    if minutes == 0:
        return minutes
    elif 0 < minutes <= 5:
        return 5
    elif 5 < minutes <= 15:
        return 15
    elif 15 < minutes <= 30:
        return 30
    elif 30 < minutes <= 45:
        return 45
    return 60


config = {
    'excluded_projects': [

    ],
    'log_level': 'warn',
    'tablefmt': 'simple',
}

with open('config.yml', 'r') as fp:
    config.update(yaml.safe_load(fp))

if not config['verify']:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SINCE = UNTIL = datetime.now().strftime('%Y-%m-%d')

pl = PL(
    app_key=config['app_key'],
    base_url=config['base_url'],
    log_level=config['log_level'],
    user_key=config['user_key'],
    verify=config['verify']
)
toggl = TogglReportsClient(api_token=config['api_token'], user_agent=config['app_key'])

config['workspace'] = toggl.select_workspace(workspace=config['workspace'])


# TODO: Move this code to PL class method or call this code as function
pl_projects = dict()
for project in pl.list_projects()['projects']:
    if project['name'] in config['excluded_projects']:
        continue
    project['tasks'] = dict()
    for task in pl.list_tasks(project_id=project['id'])['tasks']['data']:
        project['tasks'][task['title']] = task
    pl_projects.update(
        {
            project['name']: project
        }
    )

# TODO: Move this code to PL class method or call this code as function
tasks = dict()
for task in toggl.details(workspace=config['workspace'], since=SINCE, until=UNTIL)['data']:
    # GOTCHA: We want to have at least the next information about task: client, project and description. In case some
    # field is not filed the program must exit and ask to fill task details before continue with export.
    if None in (task['client'], task['project'], task['description']):
        sys.exit(yaml.dump(task))
    duration = int(task['dur'] / 1000)
    if task['client'] not in tasks:
        tasks.update(
            {
                task['client']: {
                    task['project']: {
                        task['description']: duration
                    }
                }
            }
        )
        continue
    if task['project'] not in tasks[task['client']]:
        tasks[task['client']][task['project']] = {
            task['description']: duration
        }
        continue
    if task['description'] not in tasks[task['client']][task['project']]:
        tasks[task['client']][task['project']].update(
            {
                task['description']: duration
            }
        )
        continue
    tasks[task['client']][task['project']][task['description']] += duration

posts = list()
headers = ('Client', 'Project', 'Description', 'Duration (min)', 'Rounded (min)')
for client, projects in sorted(tasks.items()):
    for project, data in sorted(projects.items()):
        for description, duration in sorted(data.items()):
            minutes, seconds = divmod(duration, 60)
            duration = minutes + round(seconds / 60)
            hours, minutes = divmod(duration, 60)
            posts.append(
                [
                    client,
                    project,
                    '\n'.join(textwrap.wrap(description, width=80)),
                    duration,
                    hours * 60 + rounded(minutes)
                ]
            )

print(tabulate(tabular_data=posts, headers=headers, tablefmt=config['tablefmt']))

try:
    input('\nPress Enter to continue or Ctrl-C to abort...')
except KeyboardInterrupt:
    sys.exit('\nExport interrupted, cancelling operation...')

for post in posts:
    print(
        pl.add_post(
            project_id=pl_projects[post[0]]['id'],
            task_id=pl_projects[post[0]]['tasks'][post[1]]['id'],
            description=post[2],
            date=SINCE,
            taken=post[4]
        )
    )
