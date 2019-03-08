import logging
import requests
import sys


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
        self.verify = verify

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
        for item in items:
            items[item.replace('_', '-')] = items.pop(item)
        return items

    def post(self, endpoint, **kwargs):
        """
        Prepare provided keyword arguments and send them to the specified PL API endpoint using HTTP POST request.
        :param endpoint: The PL API endpoint to send data using HTTP POST request.
        :type endpoint: str
        :param kwargs: Request parameters specific to each endpoint (please see the official PL API reference).
        :return: Dictionary object with remote PL API response content.
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
