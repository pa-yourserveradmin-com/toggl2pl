from datetime import datetime
from pathlib import Path
from tabulate import tabulate
from tqdm import tqdm
from time import sleep
from toggl2pl import PL
from toggl2pl import TogglReportsClient
import argparse
import os
import platform
import sys
import yaml


# The required PL application key used to gather application usage statistic
APP_KEY = 'fba04c0786f881822dd9f7aa0d2530c6:o@$s^^JG8a4w9lgJcPH*'
CONFIG_PATH = '/.toggl2pl/config.yml'
if platform.system() == 'Windows':
    CONFIG_PATH = CONFIG_PATH.replace('/', '\\')
ROUND_BASE = os.getenv('ROUND_BASE', 5)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='Path to configuration file (default: ~{config})'.format(config=CONFIG_PATH),
        type=str,
        default='{home}{config}'.format(home=str(Path.home()), config=CONFIG_PATH)
    )
    parser.add_argument(
        '-d',
        '--date',
        help='The date when work was actually done in `YYYY-MM-DD` format (default: current day).',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d')
    )
    parser.add_argument(
        '-r',
        '--round',
        help='Round the number of minutes spent on each project to +/- {} minutes.'.format(ROUND_BASE),
        action='store_true'
    )
    return parser


def main():
    known_args, unknown_args = parse_arguments().parse_known_args()
    try:
        with open(known_args.config, 'r') as fp:
            config = yaml.safe_load(fp)
    except FileNotFoundError as nf:
        sys.exit(nf)

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

    toggl_projects = toggl.projects(workspace=config['toggl']['workspace'])

    for project in projects:
        if project not in clients:
            client = toggl.create_client(name=project, workspace=config['toggl']['workspace'])
            clients.update(
                {
                    client['name']: client
                }
            )
            del clients[client['name']]['name']
            sleep(0.5)
        if clients[project]['id'] not in toggl_projects:
            toggl_projects.update(
                {
                    clients[project]['id']: [

                    ]
                }
            )
        for item in projects[project]['tasks']:
            if item not in toggl_projects[clients[project]['id']]:
                toggl.create_project(cid=clients[project]['id'], name=item, wid=config['toggl']['workspace']['id'])
                sleep(0.5)

    posts = toggl.posts(workspace=config['toggl']['workspace'], since=known_args.date, until=known_args.date)

    if not posts:
        sys.exit('There are no posts for {} yet. Please post something and try again.'.format(known_args.date))

    headers = ('Client', 'Project', 'Description', 'Duration (min)', 'Rounded (min)')
    print(tabulate(tabular_data=posts, headers=headers, tablefmt=config['tablefmt']))

    try:
        input('\nPress Enter to continue or Ctrl-C to abort...')
    except KeyboardInterrupt:
        sys.exit('\nExport interrupted, cancelling operation...')

    for post in tqdm(posts, desc='posts'):
        client, project, description, duration, rounded = post
        pl.add_post(
            project_id=projects[client]['id'],
            task_id=projects[client]['tasks'][project]['id'],
            description=description,
            date=known_args.date,
            taken=rounded if known_args.round else duration
        )
