#!/usr/bin/env python3

from datetime import datetime
from tabulate import tabulate
from toggl2pl import PL
from toggl2pl import TogglReportsClient
import argparse
import os
import sys
import yaml


# The required PL application key used to gather application usage statistic
APP_KEY = '5e0e5efeea6b4c3833729529667e458b:tIZ9qXPs(HNV&33Q3yT('

parser = argparse.ArgumentParser()
parser.add_argument(
    '-c',
    '--config',
    help='Path to configuration file (default: ~/.vault-shell/config.yml)',
    type=str,
    default='{}/.vault-shell/config.yml'.format(os.getenv('HOME'))
)
parser.add_argument(
    '-d',
    '--date',
    help='The date when work was actually done in `YYYY-MM-DD` format (default: current day).',
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
if isinstance(config['toggl']['workspace'], list) or not config['toggl']['workspace']:
    sys.exit(yaml.dump(config['toggl']['workspace']))

clients = toggl.clients(workspace=config['toggl']['workspace'])
projects = pl.projects(excluded_projects=config['pl']['excluded_projects'])

for project in projects:
    if project not in clients:
        client = toggl.create_client(name=project, workspace=config['toggl']['workspace'])
        clients.update(
            {
                client['name']: client
            }
        )
        del clients[client['name']]['name']

posts = toggl.posts(workspace=config['toggl']['workspace'], since=known_args.date, until=known_args.date)

if not posts:
    sys.exit('There are no posts for {} yet. Please post something and try again.'.format(known_args.date))

headers = ('Client', 'Project', 'Description', 'Duration (min)', 'Rounded (min)')
print(tabulate(tabular_data=posts, headers=headers, tablefmt=config['tablefmt']))

try:
    input('\nPress Enter to continue or Ctrl-C to abort...')
except KeyboardInterrupt:
    sys.exit('\nExport interrupted, cancelling operation...')

for post in posts:
    client, project, description, duration, rounded = post
    print(
        pl.add_post(
            project_id=projects[client]['id'],
            task_id=projects[client]['tasks'][project]['id'],
            description=description,
            date=known_args.date,
            taken=rounded
        )
    )
