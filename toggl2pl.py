#!/usr/bin/env python3

from datetime import datetime
from tabulate import tabulate
from toggl2pl import PL
from toggl2pl import TogglReportsClient
import argparse
import os
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


# The required PL application key used to gather application usage statistic
APP_KEY = '5e0e5efeea6b4c3833729529667e458b:tIZ9qXPs(HNV&33Q3yT('

parser = argparse.ArgumentParser()
parser.add_argument(
    '-c',
    '--config',
    help='Path to configuration file (default: {}/.vault-shell/config.yml)'.format(os.environ['HOME']),
    type=str,
    default='{}/.vault-shell/config.yml'.format(os.getenv('HOME'))
)
parser.add_argument(
    '-d',
    '--date',
    help='The date when work was actually done in `YYYY-MM-DD` format (ISO 8601).',
    type=str,
    default=datetime.now().strftime('%Y-%m-%d')
)
known_args, unknown_args = parser.parse_known_args()

with open(known_args.config, 'r') as fp:
    config = yaml.safe_load(fp)

pl = PL(
    app_key=APP_KEY,
    base_url=config['pl']['base_url'],
    log_level=config['log_level'],
    user_key=config['pl']['user_key'],
    verify=config['pl']['verify']
)
toggl = TogglReportsClient(api_token=config['toggl']['api_token'], user_agent=APP_KEY)

config['toggl']['workspace'] = toggl.workspaces(name=config['toggl']['workspace'])
if not config['toggl']['workspace'] or len(config['toggl']['workspace']) > 1:
    sys.exit(yaml.dump(config['toggl']['workspace']))


# TODO: Move this code to PL class method or call this code as function
pl_projects = dict()
for project in pl.list_projects()['projects']:
    if project['name'] in config['pl']['excluded_projects']:
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
for task in toggl.details(workspace=config['toggl']['workspace'], since=known_args.date, until=known_args.date)['data']:
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
            date=known_args.date,
            taken=post[4]
        )
    )
