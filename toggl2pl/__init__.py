import logging
import requests
import sys
import urllib3


class PL(object):

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

    # TODO: Merge select_workspace() and workspaces() methods into workspaces() method with optional filter argument.
    def select_workspace(self, workspace):
        """
        Iterate over list of workspaces available for specified API token and select one based on workspace name.
        :param workspace: The name of Toggl workspace to fetch details about.
        :type workspace: str
        :return: Dictionary object with details about requested workspace.
        :rtype: dict
        """
        for item in self.workspaces():
            if item['name'] == workspace:
                return item

    def workspaces(self):
        """
        List all workspaces available for specified API token.
        :return: List of dictionaries which represent workspaces available for specified API token.
        :rtype: list
        """
        return self.get(endpoint='workspaces', url=self.toggl_api_url)


class TogglReportsClient(TogglAPIClient):

    base_url = 'https://toggl.com'

    reports_api_version = 2
    reports_api_url = '{}/reports/api/v{}'.format(base_url, reports_api_version)

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
