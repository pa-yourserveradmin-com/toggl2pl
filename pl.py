#!/usr/bin/env python3

from tabulate import tabulate
from toggl2pl import PL
import yaml

config = {
    'excluded_projects': [

    ],
    'log_level': 'warn',
    'tablefmt': 'simple'
}

headers = ('Client', 'Project', 'Status', 'Assigned')
rows = list()

with open('config.yml', 'r') as fp:
    config.update(yaml.safe_load(fp))

if not config['verify']:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

pl = PL(
    app_key=config['app_key'],
    base_url=config['base_url'],
    log_level=config['log_level'],
    user_key=config['user_key'],
    verify=config['verify']
)

for project in pl.list_projects()['projects']:
    if project['name'] in config['excluded_projects']:
        continue
    for task in pl.list_tasks(project_id=project['id'])['tasks']['data']:
        rows.append([project['name'], task['title'], task['status'], task['assigned']])

print(tabulate(tabular_data=rows, headers=headers, tablefmt=config['tablefmt']))
