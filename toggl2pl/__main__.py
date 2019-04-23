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


def load_config(config):
    """
    Load configuration from supplied YAML formatted file.

    :param config: The relative or absolute path to YAML configuration file.
    :type config: str
    :return: Dictionary object with configuration options loaded from file.
    :rtype: dict
    """
    try:
        with open(config, 'r') as fp:
            return yaml.safe_load(fp)
    except FileNotFoundError as nf:
        sys.exit(nf)


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
        '-s',
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
    parser.set_defaults(func=run)
    subparsers = parser.add_subparsers()
    serve = subparsers.add_parser(name='serve', help='Start application in server mode (not yet implemented).')
    serve.add_argument('-i', '--ipv4', type=str, help='The IPv4 address to run application on.', default='0.0.0.0')
    serve.add_argument('-p', '--port', type=int, help='The TCP port to run application on.', default=5000)
    serve.set_defaults(func=start)
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


def run(known_args):
    """
    Run application in client mode (the way how to communicate with trackers depends on configuration file).

    :param known_args: The argument parser namespace object with supplied arguments.
    :type known_args: :obj:`argparse.Namespace`
    """
    config = load_config(config=known_args.config)
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
    try:
        posts = review(
            posts=client.posts(
                since=known_args.date,
                until=known_args.date
            ),
            why_run=known_args.why_run
        )
    except AssertionError as ae:
        sys.exit(yaml.dump(ae.args[0], allow_unicode=True))
    for post in tqdm(posts, desc='posts'):
        project, task, description, duration, rounded = post
        client.add_post(
            date=known_args.date,
            description=description,
            minutes=rounded if known_args.round else duration,
            project=project,
            task=task,
        )


def start(known_args):
    """
    Start application in server mode to serve incoming HTTP requests and process data received from clients.

    :param known_args: The argument parser namespace object with supplied arguments.
    :type known_args: :obj:`argparse.Namespace`
    """
    raise NotImplementedError('Server mode is not yet implemented')


def main():
    """
    Main entry point used by toggl2pl script to process command line arguments and start application.
    """
    known_args, unknown_args = parse_arguments().parse_known_args()
    known_args.func(known_args=known_args)
