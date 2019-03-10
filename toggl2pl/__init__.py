import logging
import requests
import sys
import textwrap
import urllib3
import yaml


class PL(object):

    cache = {
        'projects': {

        }
    }

    def __init__(self, app_key, base_url, user_key, log_level='warning', verify=True):
        """
        Initialize a new instance of class object to communicate with PL.
        :param app_key: The required application key used to gather application usage statistic.
        :type app_key: str
        :param base_url: The PL API base URL in format `<scheme>://<domain>/<uri>`.
        :type base_url: str
        :param user_key: The unique authentication token to use instead of username and password.
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

    def add_post(self, project_id, task_id, description, date, taken):
        """
        Create new post in PL database related to corresponding project and task with such required information as date,
        description and time taken.
        :param project_id: The project ID in PL database corresponding task belongs to.
        :type project_id: int
        :param task_id: The task ID in PL database to create new post.
        :type task_id: int
        :param description: Relatively short description of the work done as a part of the parent task.
        :type description: str
        :param date: The date when work was actually done in `YYYY-MM-DD` format (ISO 8601).
        :type date: str
        :param taken: Total amount of minutes spent during work on the task entry.
        :type taken: int
        :return: Dictionary object with PL API response content.
        :rtype: dict
        """
        return self.post(
            endpoint='posts/add',
            project_id=project_id,
            task_id=task_id,
            description=description,
            date=date,
            taken=taken
        )

    def list(self, endpoint, **kwargs):
        """
        Wrapper for `PL.post()` method especially to execute requests to `list` PL endpoints.
        :param endpoint: The PL entity (projects, tasks and so on) to list objects via API request.
        :type endpoint: str
        :param kwargs: Request parameters specific to each entity (please see the official PL API reference).
        :return: Dictionary object with list of requested PL entities.
        :rtype: dict
        """
        return self.post(endpoint='{}/list'.format(endpoint), **kwargs)

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

    def list_tasks(self, project_id):
        """
        List tasks corresponding to the particular project specified by its ID.
        :param project_id: The parent object ID to query list of tasks.
        :type project_id: int
        :return: Dictionary object with list of PL tasks related to requested project.
        :rtype: dict
        """
        return self.list(endpoint='tasks', project_id=project_id, per_page=-1)

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
                url='{}/{}'.format(self.base_url, endpoint),
                json=kwargs,
                verify=self.verify
            )
            if response.status_code != 200:
                logging.error(msg=response.content)
                sys.exit(response.status_code)
            return response.json()
        except Exception as ex:
            sys.exit(ex)

    def projects(self, excluded_projects=None, refresh=False):
        """
        Wrapper for `list_projects` and `list_tasks` methods to exclude particular PL projects and combine projects data
        with tasks data into single object with machine-readable structure. Uses internal instance cache to store data
        between calls.
        :param excluded_projects: List of PL projects names to exclude from result.
        :type excluded_projects: list
        :param refresh: Optional argument to force refresh data cached on PL object instance level.
        :type refresh: bool
        :return: Dictionary object with combined information about PL projects and their tasks.
        :rtype: dict
        """
        if self.cache['projects'] and not refresh:
            return self.cache['projects']
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
        self.cache['projects'] = projects
        return projects


class TogglAPIClient(object):

    base_url = 'https://toggl.com'

    toggl_api_version = 8
    toggl_api_url = '{}/api/v{}'.format(base_url, toggl_api_version)

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

    def clients(self, workspace):
        """
        Wrapper for `list_clients` method to convert list of Toggl clients into machine-readable format.
        :param workspace: Dictionary object which represents Toggl workspace.
        :type workspace: dict
        :return: Dictionary object with detailed information about Toggl clients.
        :rtype: dict
        """
        clients = dict()
        for client in self.list_clients(workspace=workspace):
            clients[client['name']] = client
            del clients[client['name']]['name']
        return clients

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
                url='{}/{}'.format(url, endpoint),
                auth=self.auth,
                params=kwargs
            )
            if response.status_code != 200:
                logging.error(msg=response.content)
                sys.exit(response.status_code)
            return response.json()
        except Exception as ex:
            sys.exit(ex)

    def list_clients(self, workspace):
        """
        List clients corresponding to the particular Toggl workspace.
        :param workspace: Dictionary object which represents Toggl workspace.
        :type workspace: dict
        :return: List of dictionaries with clients descriptions.
        :rtype: list
        """
        return self.get(endpoint='workspaces/{}/clients'.format(workspace['id']))

    def workspaces(self, name=str()):
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
    reports_api_url = '{}/reports/api/v{}'.format(base_url, reports_api_version)

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
            description = '* {}'.format(description)
        if not description.endswith('.'):
            description += '.'
        description = '\n'.join(textwrap.wrap(description.strip(), width=width))
        return description

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

    def details(self, workspace, **kwargs):
        """
        Fetch detailed information about tasks related to the specified Toggl workspace.
        :param workspace: Toggl workspace to query information about tasks.
        :type workspace: dict
        :param kwargs: Parameters to query Toggl Reports API (please see official Toggl Reports API for details).
        :return: Dictionary object with detailed information about recorded tasks.
        :rtype: dict
        """
        kwargs.update(
            {
                'user_agent': self.user_agent,
                'workspace_id': workspace['id']
            }
        )
        return self.get(
            endpoint='details',
            **kwargs
        )

    def list_clients(self, workspace):
        """
        List clients corresponding to the particular Toggl workspace.
        :param workspace: Dictionary object which represents Toggl workspace.
        :type workspace: dict
        :return: List of dictionaries with clients descriptions.
        :rtype: list
        """
        return super().get(endpoint='workspaces/{}/clients'.format(workspace['id']))

    def posts(self, workspace, since, until):
        """
        High-level wrapper for `tasks` method to aggregate Toggl tasks by projects, format descriptions and round total
        amount of minutes per project.
        :param workspace: Dictionary object which represents Toggl workspace.
        :type workspace: dict
        :param since: The start date in ISO 8601 date (YYYY-MM-DD) format to query Toggl Reports API for tasks.
        :type since: str
        :param until: The end date in ISO 8601 date (YYYY-MM-DD) format to query Toggl Reports API for tasks.
        :type until: str
        :return: Normalized list of Toggl tasks aggregated by projects.
        :rtype: list
        """
        posts = list()
        for client, projects in sorted(self.tasks(workspace, since, until).items()):
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

    def tasks(self, workspace, since, until):
        """
        Combine clients, projects and tasks information into single object with machine-readable format.
        :param workspace: Dictionary object which represents Toggl workspace.
        :type workspace: dict
        :param since: The start date in ISO 8601 date (YYYY-MM-DD) format to query Toggl Reports API for tasks.
        :type since: str
        :param until: The end date in ISO 8601 date (YYYY-MM-DD) format to query Toggl Reports API for tasks.
        :type until: str
        :return: Dictionary object with machine-readable information about Toggl tasks during specified range of dates.
        :rtype: dict
        """
        tasks = dict()
        for task in self.details(workspace=workspace, since=since, until=until)['data']:
            # GOTCHA: We want to have at least the next information about task: client, project and description. In case
            # some field is not filed the program must exit and ask to fill task details before continue with export.
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
        return tasks


def rounded(minutes):
    """
    Round the number of provided minutes based on the amount of minutes.
    :param minutes: Real number of minutes to apply round operation on.
    :type minutes: int
    :return: Number of minutes rounded based on amount og real amount of minutes.
    :rtype: int
    """
    if minutes == 0:
        return 5
    elif 0 < minutes <= 5:
        return 5
    elif 5 < minutes <= 15:
        return 15
    elif 15 < minutes <= 30:
        return 30
    elif 30 < minutes <= 45:
        return 45
    return 60
