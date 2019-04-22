from datetime import datetime
from pathlib import Path
from tabulate import tabulate
from tqdm import tqdm
from toggl2pl import Client
import argparse
import os
import platform
import sys
import yaml


CONFIG_PATH = '/.toggl2pl/config.yml'
if platform.system() == 'Windows':
    CONFIG_PATH = CONFIG_PATH.replace('/', '\\')

ROUND_BASE = os.getenv('ROUND_BASE', 5)


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
        help='Path to configuration file (default: ~{config}).'.format(config=CONFIG_PATH),
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
        help='Start application in server mode (not yet implemented).',
        action='store_true'
    )
    parser.add_argument(
        '--sync',
        help='Synchronize projects and tasks between time trackers.',
        action='store_true'
    )
    parser.add_argument(
        '-w',
        '--why-run',
        help='Run client in why-run mode to preview posts without publishing.',
        action='store_true'
    )
    return parser


def review(posts, tablefmt='fancy_grid', why_run=False):
    """
    Print data into standard output and ask about confirmation before actual data import/export.

    :param posts: List of posts imported from source time tracker and to be published into target tracker during export.
    :type posts: list
    :param tablefmt: The table format to use (recommended formats are: plain, simple, rst and fancy_grid).
    :type tablefmt: str
    :param why_run: Optional flag to enable `why-run` mode (preview posts without publishing).
    :type why_run: bool
    :return: The provided list of posts without any modifications.
    :rtype: list
    """
    headers = ('Project', 'Task', 'Description', 'Real Duration (min)', 'Rounded Duration (min)')
    print(tabulate(tabular_data=posts, headers=headers, tablefmt=tablefmt))
    if not why_run:
        try:
            input('\nPress Enter to continue or Ctrl-C to abort...')
        except KeyboardInterrupt:
            sys.exit('\nExport interrupted, cancelling operation...')
        return posts
    sys.exit()


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

    client = Client(
        api_token=config['toggl']['api_token'],
        base_url=config['pl']['base_url'],
        excluded_projects=config['pl']['excluded_projects'],
        log_level=config['log_level'],
        user_key=config['pl']['user_key'],
        verify=config['pl']['verify'],
        workspace=config['toggl']['workspace']
    )

    if known_args.sync:
        client.sync()

    posts = review(
        posts=client.posts(
            since=known_args.date,
            until=known_args.date
        ),
        why_run=known_args.why_run
    )

    for post in tqdm(posts, desc='posts'):
        project, task, description, duration, rounded = post
        client.add_post(
            date=known_args.date,
            description=description,
            minutes=rounded if known_args.round else duration,
            project=project,
            task=task,
        )
