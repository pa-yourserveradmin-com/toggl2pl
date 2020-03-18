from time import sleep
import logging
import requests
import sys
import textwrap
import urllib3
import yaml

# The required PL application key used to gather application usage statistic
APP_KEY = 'fba04c0786f881822dd9f7aa0d2530c6:o@$s^^JG8a4w9lgJcPH*'


class Client(object):

    def __init__(self, api_token, base_url, user_key, workspace, excluded_projects=None, log_level='info', verify=True):
        """
        High-level class which aggregates common methods required to pull, push and sync data between Project Laboratory
        and Toggl.

        :param api_token: The Toggl authentication token to use instead of username and password.
        :type api_token: str
        :param base_url: The Project Laboratory API base URL in format `<scheme>://<domain>/<uri>`.
        :type base_url: str
        :param user_key: The Project Laboratory authentication token to use instead of username and password.
        :type user_key: str
        :param workspace: The Toggl workspace name (case sensitive) to pull information from.
        :type workspace: str
        :param excluded_projects: Optional list of Project Laboratory projects names to exclude from pull.
        :type excluded_projects: list
        :param log_level: Optional logging level name to configure logging verbosity (default: `info`).
        :type log_level: str
        :param verify: Optional argument which allows to disable TLS connection verification and suppress warnings.
        :type verify: bool
        """
        self.pl = PL(
            app_key=APP_KEY,
            base_url=base_url,
            log_level=log_level,
            user_key=user_key,
            verify=verify
        )
        self.projects = self.pl.projects(excluded_projects=excluded_projects)
        self.toggl = TogglReportsClient(api_token=api_token, user_agent=APP_KEY)
        self.me = self.toggl.me()
        self.workspace = self.check_workspace(workspace=self.toggl.workspaces(name=workspace))

    def add_post(self, date, description, minutes, project, task):
        """
        Create a new post in Project Laboratory about specific task execution details.

        :param date: The date when work was actually done in ISO 8601 (`YYYY-MM-DD`) format.
        :type date: str
        :param description: Relatively short description of the work done as a part of the parent task.
        :type description: str
        :param minutes: Total amount of minutes spent during work on the task entry.
        :type minutes: int
        :param project: The project name in Project Laboratory database corresponding task belongs to.
        :type project: int
        :param task: The task name in Project Laboratory database to create new post.
        :type task: int
        :return: Dictionary object with PL API response content.
        :rtype: dict
        """
        return self.pl.add_post(
            date=date,
            description=description,
            minutes=minutes,
            project_id=self.projects[project]['id'],
            task_id=self.projects[project]['tasks'][task]['id']
        )

    @staticmethod
    def check_workspace(workspace):
        """
        Check provided Toggl workspace data format and value.

        :param workspace: Toggl workspace data to check.
        :type workspace: dict
        :return: Dictionary object which represents single Toggl workspace.
        :rtype: dict
        :raises TypeError: In case provided workspace data has type `list` or `None`.
        """
        if isinstance(workspace, list) or not workspace:
            raise TypeError(yaml.dump(workspace))
        return workspace

    def posts(self, since, until):
        """
        Wrapper for :meth:`TogglReportsClient.posts` to pull list of Toggl posts between since and until dates.

        :param since: The start date in ISO 8601 (`YYYY-MM-DD`) format to query Toggl Reports API for tasks.
        :type since: str
        :param until: The end date in ISO 8601 (`YYYY-MM-DD`) format to query Toggl Reports API for tasks.
        :type until: str
        :return: Normalized list of Toggl tasks aggregated by projects.
        :rtype: list
        """
        return self.toggl.posts(since=since, until=until, wid=self.workspace['id'])

    def sync(self):
        """
        Synchronize projects and tasks from Project Laboratory into Toggl.
        """
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


class PL(object):

    def __init__(self, app_key, base_url, user_key, log_level='info', verify=True):
        """
        Initialize a new instance of class object to communicate with PL.

        :param app_key: The required application key used to gather application usage statistic.
        :type app_key: str
        :param base_url: The Project Laboratory API base URL in format `<scheme>://<domain>/<uri>`.
        :type base_url: str
        :param user_key: The Project Laboratory authentication token to use instead of username and password.
        :type user_key: str
        :param verify: Optional argument which allows to disable TLS connection verification and suppress warnings.
        :type verify: bool
        """
        logging.basicConfig(level=logging.getLevelName(log_level.upper()))
        self.base_url = base_url
        self.data = {
            'app-key': app_key,
            'user-key': user_key
        }
        self.session = requests.Session()
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.verify = verify

    def add_post(self, date, description, minutes, project_id, task_id):
        """
        Create a new post in Project Laboratory about specific task execution details.

        :param date: The date when work was actually done in `YYYY-MM-DD` format (ISO 8601).
        :type date: str
        :param description: Relatively short description of the work done as a part of the parent task.
        :type description: str
        :param minutes: Total amount of minutes spent during work on the task entry.
        :type minutes: int
        :param project_id: The project ID in PL database corresponding task belongs to.
        :type project_id: int
        :param task_id: The task ID in PL database to create new post.
        :type task_id: int
        :return: Dictionary object with PL API response content.
        :rtype: dict
        """
        return self.post(
            endpoint='posts/add',
            project_id=project_id,
            task_id=task_id,
            description=description,
            date=date,
            taken=minutes
        )

    def list(self, endpoint, **kwargs):
        """
        Wrapper for :meth:`post` method especially to execute requests to PL `list` endpoints.

        :param endpoint: The PL entity (projects, tasks and so on) to list objects via API request.
        :type endpoint: str
        :param kwargs: Request parameters specific to each entity (please see the official PL API reference).
        :return: Dictionary object with list of requested PL entities.
        :rtype: dict
        """
        return self.post(endpoint='{endpoint}/list'.format(endpoint=endpoint), **kwargs)

    def list_projects(self, include_inactive=False):
        """
        List projects visible for the provided `user-key` (i.e. only list projects the provided `user-key` is authorized
        to view).

        :param include_inactive: Optional argument which allows to include inactive tasks in the result list.
        :type include_inactive: bool
        :return: Dictionary object with list of PL projects visible for the `user-key`.
        :rtype: dict
        """
        return self.list(endpoint='projects', include_inactive=include_inactive)

    def list_tasks(self, project_id, per_page=-1):
        """
        List tasks corresponding to the particular project specified by its ID.

        :param project_id: The parent object ID to query list of tasks.
        :type project_id: int
        :param per_page: The maximum number of projects to return in response.
        :type per_page: int
        :return: Dictionary object with list of PL tasks related to requested project.
        :rtype: dict
        """
        return self.list(endpoint='tasks', project_id=project_id, per_page=per_page)

    @staticmethod
    def normalize(items):
        """
        Helper function to normalize dictionaries keys and make them compatible with PL API request parameters names.

        :param items: Dictionary object with request parameters to normalize before send request to remote PL API.
        :type items: dict
        :return: Dictionary object with keys updated according to PL API specific (hyphens instead of underscores).
        :rtype: dict
        """
        results = dict()
        for item in items:
            results[item.replace('_', '-')] = items[item]
        return results

    def post(self, endpoint, **kwargs):
        """
        Prepare provided keyword arguments and send them to the specified PL API endpoint using HTTP POST request.

        :param endpoint: The PL API endpoint to send data using HTTP POST request.
        :type endpoint: str
        :param kwargs: Request parameters specific to each endpoint (please see the official PL API reference).
        :return: Dictionary object with PL API endpoint response content.
        :rtype: dict
        """
        kwargs = self.normalize(items=kwargs)
        kwargs.update(self.data)
        try:
            response = self.session.post(
                url='{base_url}/{endpoint}'.format(base_url=self.base_url, endpoint=endpoint),
                json=kwargs,
                verify=self.verify
            )
            logging.debug(msg=kwargs)
            if response.status_code != 200:
                sys.exit('{status_code}: {content}'.format(status_code=response.status_code, content=response.content))
            return response.json()
        except Exception as ex:
            sys.exit(ex)

    def projects(self, excluded_projects=None):
        """
        Wrapper for :meth:`list_projects` and :meth:`list_tasks` methods to combine projects data with tasks data into
        single object with machine-readable structure and optionally to exclude particular PL projects.

        :param excluded_projects: List of PL projects names to exclude from result.
        :type excluded_projects: list
        :return: Dictionary object with combined information about PL projects and their tasks.
        :rtype: dict
        """
        projects = dict()
        for project in self.list_projects()['projects']:
            if excluded_projects and project['name'] in excluded_projects:
                continue
            project['tasks'] = dict()
            for task in self.list_tasks(project_id=project['id'])['tasks']['data']:
                project['tasks'][task['title']] = task
            projects.update(
                {
                    project['name']: project
                }
            )
        return projects


class TogglAPIClient(object):

    base_url = 'https://toggl.com'

    toggl_api_version = 8
    toggl_api_url = '{base_url}/api/v{toggl_api_version}'.format(base_url=base_url, toggl_api_version=toggl_api_version)

    def __init__(self, api_token, user_agent):
        """
        Initialize a new instance of class object to communicate with Toggl.

        :param api_token: The unique authentication token to use instead of username and password.
        :type api_token: str
        :param user_agent: The required user agent identifier used to gather application usage statistic.
        :type user_agent: str
        """
        self.auth = (api_token, 'api_token')
        self.session = requests.Session()
        self.user_agent = user_agent

    def clients(self, wid):
        """
        Wrapper for :meth:`list_clients` method to convert list of Toggl clients into machine-readable format.

        :param wid: The unique Toggl workspace ID to list clients.
        :type wid: int
        :return: Dictionary object with detailed information about Toggl clients.
        :rtype: dict
        """
        clients = dict()
        for client in self.list_clients(wid=wid):
            clients[client['name']] = client
            del clients[client['name']]['name']
        return clients

    def create_client(self, name, wid):
        """
        Create a new client in the particular Toggl workspace.

        :param name: The client name to create in Toggl workspace.
        :type name: str
        :param wid: The unique Toggl workspace ID to create client.
        :type wid: int
        :return: Dictionary object with information about the newly created Toggl client.
        :rtype: dict
        """
        return self.post(
            endpoint='clients',
            client={
                'name': name,
                'wid': wid
            }
        )['data']

    def create_project(self, cid, name, wid):
        """
        Create a new client project in the particular Toggl workspace.

        :param cid: The client ID to associate project with.
        :type cid: int
        :param name: The name to use for a new project.
        :type name: str
        :param wid: The unique Toggl workspace ID to create project.
        :type wid: int
        :return: Dictionary object with information about the newly created Toggl project.
        :rtype: dict
        """
        return self.post(
            endpoint='projects',
            project={
                'cid': cid,
                'name': name,
                'wid': wid
            }
        )['data']

    def get(self, endpoint, url=toggl_api_url, **kwargs):
        """
        Send provided keyword arguments to the combination of Toggl API URL and endpoint using HTTP GET request.

        :param endpoint: The Toggl API endpoint to send data using HTTP GET request.
        :type endpoint: str
        :param url: The Toggl API URL to send HTTP GET requests.
        :type url: str
        :param kwargs: Request parameters specific to each endpoint (please see the official Toggl API reference).
        :return: Dictionary object with Toggl API endpoint response content.
        :rtype: dict
        """
        try:
            response = self.session.get(
                url='{url}/{endpoint}'.format(url=url, endpoint=endpoint),
                auth=self.auth,
                params=kwargs
            )
            logging.debug(msg=kwargs)
            if response.status_code != 200:
                sys.exit('{status_code}: {content}'.format(status_code=response.status_code, content=response.content))
            return response.json()
        except Exception as ex:
            sys.exit(ex)

    def list_clients(self, wid):
        """
        List clients corresponding to the particular Toggl workspace.

        :param wid: The unique Toggl workspace ID to list clients.
        :type wid: int
        :return: List of dictionaries with clients descriptions.
        :rtype: list
        """
        clients = self.get(endpoint='workspaces/{wid}/clients'.format(wid=wid))
        if clients:
            return clients
        return dict()

    def me(self):
        """
        Fetch information about the currently authenticated user account.

        :return: Dictionary object with information about the currently authenticated user account.
        :rtype: dict
        """
        return self.get(endpoint='me')['data']

    def post(self, endpoint, url=toggl_api_url, **kwargs):
        """
        Send provided keyword arguments to the combination of Toggl API URL and endpoint using HTTP POST request.

        :param endpoint: The Toggl API endpoint to send data using HTTP POST request.
        :type endpoint: str
        :param url: The Toggl API URL to send HTTP POST requests.
        :type url: str
        :param kwargs: Request payload specific to each endpoint (please see the official Toggl API reference).
        :return: Dictionary object with Toggl API endpoint response content.
        :rtype: dict
        """
        try:
            response = self.session.post(
                url='{url}/{endpoint}'.format(url=url, endpoint=endpoint),
                auth=self.auth,
                json=kwargs
            )
            logging.debug(msg=kwargs)
            if response.status_code != 200:
                sys.exit('{status_code}: {content}'.format(status_code=response.status_code, content=response.content))
            return response.json()
        except Exception as ex:
            sys.exit(ex)

    def workspaces(self, name=None):
        """
        List workspaces available for specified API token with optional ability to query single workspace by its name.

        :param name: The optional workspace name to filter results.
        :type name: str
        :return: Dictionary object which represents single or all workspaces available for specified API token.
        :rtype: dict
        """
        workspaces = self.get(endpoint='workspaces', url=self.toggl_api_url)
        if name:
            for workspace in workspaces:
                if workspace['name'] == name:
                    return workspace
        return workspaces


class TogglReportsClient(TogglAPIClient):

    base_url = 'https://toggl.com'

    reports_api_version = 2
    reports_api_url = '{base_url}/reports/api/v{reports_api_version}'.format(
        base_url=base_url,
        reports_api_version=reports_api_version
    )

    @staticmethod
    def fmt(description, width=80):
        """
        Modify provided description text to make it readable and ensure all posts use the same canonical format.

        :param description: Toggl post description text to format.
        :type description: str
        :param width: Optional argument to set the maximum length of wrapped lines.
        :type width: int
        :return: Description text rewritten in canonical format.
        :rtype: str
        """
        if not description.startswith('* '):
            description = '* {description}'.format(description=description)
        if not description.endswith('.'):
            description += '.'
        return '\n'.join(textwrap.wrap(description.strip(), width=width))

    def get(self, endpoint, url=reports_api_url, **kwargs):
        """
        Send provided keyword arguments to the combination of Toggl Reports API URL and endpoint using HTTP GET request.

        :param endpoint: The Toggl Reports API endpoint to send data using HTTP GET request.
        :type endpoint: str
        :param url: The Toggl Reports API URL to send HTTP GET requests.
        :type url: str
        :param kwargs: Request parameters specific to each endpoint (please see the official Toggl API reference).
        :return: Dictionary object with Toggl Reports API endpoint response content.
        :rtype: dict
        """
        return super().get(endpoint=endpoint, url=url, **kwargs)

    def details(self, wid, **kwargs):
        """
        Fetch detailed information about tasks related to the specified Toggl workspace.

        :param wid: The Toggl workspace ID to query information about tasks.
        :type wid: int
        :param kwargs: Parameters to query Toggl Reports API (please see official Toggl Reports API for details).
        :return: Dictionary object with detailed information about recorded tasks.
        :rtype: dict
        """
        kwargs.update(
            {
                'user_agent': self.user_agent,
                'user_ids': self.me()['id'],
                'workspace_id': wid
            }
        )
        return self.get(
            endpoint='details',
            **kwargs
        )

    def list_clients(self, wid):
        """
        List clients corresponding to the particular Toggl workspace.

        :param wid: The unique Toggl workspace ID to list clients.
        :type wid: int
        :return: List of dictionaries with clients descriptions.
        :rtype: list
        """
        clients = super().get(endpoint='workspaces/{wid}/clients'.format(wid=wid))
        if clients:
            return clients
        return dict()

    def me(self):
        """
        Fetch information about the currently authenticated user account.

        :return: Dictionary object with information about the currently authenticated user account.
        :rtype: dict
        """
        return super().get(endpoint='me')['data']

    def posts(self, since, until, wid):
        """
        High-level wrapper for :meth:`tasks` method to aggregate Toggl tasks by projects, format descriptions and round
        total amount of minutes per project.

        :param since: The start date in ISO 8601 (`YYYY-MM-DD`) format to query Toggl Reports API for tasks.
        :type since: str
        :param until: The end date in ISO 8601 (`YYYY-MM-DD`) format to query Toggl Reports API for tasks.
        :type until: str
        :param wid: The unique Toggl workspace ID to list tasks.
        :type wid: int
        :return: Normalized list of Toggl tasks aggregated by projects.
        :rtype: list
        """
        posts = list()
        for client, projects in sorted(self.tasks(since, until, wid).items()):
            for project, data in sorted(projects.items()):
                durations = 0
                descriptions = list()
                for description, duration in sorted(data.items()):
                    durations += duration
                    descriptions.append(self.fmt(description=description))
                minutes, seconds = divmod(durations, 60)
                duration = minutes + round(seconds / 60)
                hours, minutes = divmod(duration, 60)
                posts.append(
                    [
                        client,
                        project,
                        '\n'.join(descriptions),
                        duration,
                        hours * 60 + rounded(minutes)
                    ]
                )
        return posts

    def projects(self, wid):
        """
        Fetch list of the particular workspace projects and rewrite it into dictionary with machine-readable structure.

        :param wid: The unique Toggl workspace ID to list projects.
        :type wid: int
        :return: Dictionary object with machine-readable information about projects in the specified workspace.
        :rtype: dict
        """
        projects = dict()
        try:
            for item in super().get(endpoint='workspaces/{wid}/projects'.format(wid=wid)):
                if item['cid'] not in projects:
                    projects.update(
                        {
                            item['cid']: [
                                item['name']
                            ]
                        }
                    )
                    continue
                projects[item['cid']].append(item['name'])
        except TypeError:
            logging.debug(msg='it looks like you do not have any Toggl projects yet')
            return projects
        return projects

    def tasks(self, since, until, wid):
        """
        Combine clients, projects and tasks information into single object with machine-readable format.

        :param since: The start date in ISO 8601 (`YYYY-MM-DD`) format to query Toggl Reports API for tasks.
        :type since: str
        :param until: The end date in ISO 8601 (`YYYY-MM-DD`) format to query Toggl Reports API for tasks.
        :type until: str
        :param wid: The unique Toggl workspace ID to list tasks.
        :type wid: int
        :return: Dictionary object with machine-readable information about Toggl tasks during specified range of dates.
        :rtype: dict
        """
        tasks = dict()
        for task in self.details(wid=wid, since=since, until=until)['data']:
            # GOTCHA: We want to have at least the next information about task: client, project and description. In case
            # some field is not filed the program must exit and ask to fill task details before continue with export.
            if None in (task['client'], task['project'], task['description']):
                raise AssertionError(
                    {
                        'client': task['client'],
                        'project': task['project'],
                        'description': task['description']
                    }
                )
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
        return tasks


def rounded(minutes, base=5):
    """
    Round the number of provided minutes based on the amount of minutes.

    :param minutes: Real number of minutes to apply round operation on.
    :type minutes: int
    :param base: The base number of minutes to use in rounding.
    :type base: int
    :return: Number of minutes rounded based on amount of real amount of minutes.
    :rtype: int
    """
    div, mod = divmod(minutes, base)
    if round(float(mod) / base):
        return div * base + 5
    return div * base
