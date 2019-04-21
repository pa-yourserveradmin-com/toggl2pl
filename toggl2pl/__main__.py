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


class Client(object):

    def __init__(self, config):
        self.pl = PL(
            app_key=APP_KEY,
            base_url=config['pl']['base_url'],
            log_level=config['log_level'],
            user_key=config['pl']['user_key'],
            verify=config['pl']['verify']
        )
        self.projects = self.pl.projects(excluded_projects=config['pl']['excluded_projects'])
        self.toggl = TogglReportsClient(api_token=config['toggl']['api_token'], user_agent=APP_KEY)
        self.workspace = check_workspace(workspace=self.toggl.workspaces(name=config['toggl']['workspace']))
        self.sync()

    def add_post(self, date, description, minutes, project_id, task_id):
        return self.pl.add_post(
            date=date,
            description=description,
            minutes=minutes,
            project_id=project_id,
            task_id=task_id
        )

    def posts(self, since, until):
        return self.toggl.posts(since=since, until=until, wid=self.workspace['id'])

    def sync(self):
        clients = self.toggl.clients(wid=self.workspace['id'])
        projects = self.toggl.projects(wid=self.workspace['id'])
        for project in self.projects:
            if project not in clients:
                client = self.toggl.create_client(name=project, wid=self.workspace['id'])
                clients.update(
                    {
                        client['name']: client
                    }
                )
                del clients[client['name']]['name']
                sleep(0.5)
            if clients[project]['id'] not in projects:
                projects.update(
                    {
                        clients[project]['id']: [

                        ]
                    }
                )
            for item in self.projects[project]['tasks']:
                if item not in projects[clients[project]['id']]:
                    self.toggl.create_project(cid=clients[project]['id'], name=item, wid=self.workspace['id'])
                    sleep(0.5)


def check_workspace(workspace):
    """
    Check provided workspace data format and value.

    :param workspace: Toggl workspace data to check.
    :type workspace: dict
    :return: Dictionary object which represents single Toggl workspace.
    :rtype: dict
    :raises TypeError: In case provided workspace data has type `list` or `None`.
    """
    if isinstance(workspace, list) or not workspace:
        raise TypeError(yaml.dump(workspace))
    return workspace


def parse_arguments():
    """
    Function to handle argument parser configuration (argument definitions, default values and so on).

    :return: :obj:`argparse.ArgumentParser` object with set of configured arguments.
    :rtype: argparse.ArgumentParser
    """
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
    parser.add_argument(
        '--serve',
        help='Start application in server mode',
        action='store_true'
    )
    return parser


def main():
    """
    Main entry point used by toggl2pl tool to process command line arguments, parse configuration file and use the
    module API to interact with time trackers.
    """
    known_args, unknown_args = parse_arguments().parse_known_args()
    try:
        with open(known_args.config, 'r') as fp:
            config = yaml.safe_load(fp)
    except FileNotFoundError as nf:
        sys.exit(nf)

    if known_args.serve:
        raise NotImplementedError('Server mode is not yet implemented')

    client = Client(config=config)
    posts = client.posts(since=known_args.date, until=known_args.date)
    if not posts:
        sys.exit('There are no posts for {} yet. Please post something and try again.'.format(known_args.date))

    headers = ('Project', 'Task', 'Description', 'Real Duration (min)', 'Rounded Duration (min)')
    print(tabulate(tabular_data=posts, headers=headers, tablefmt=config['tablefmt']))

    try:
        input('\nPress Enter to continue or Ctrl-C to abort...')
    except KeyboardInterrupt:
        sys.exit('\nExport interrupted, cancelling operation...')

    for post in tqdm(posts, desc='posts'):
        project, task, description, duration, rounded = post
        client.add_post(
            date=known_args.date,
            description=description,
            minutes=rounded if known_args.round else duration,
            project_id=client.projects[project]['id'],
            task_id=client.projects[project]['tasks'][task]['id'],
        )
