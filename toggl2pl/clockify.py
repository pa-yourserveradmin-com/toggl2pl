import logging
import requests
import sys


class Client(object):

    def __init__(self, api_key, api_url='https://api.clockify.me/api', log_level='warn'):
        logging.basicConfig(level=logging.getLevelName(log_level.upper()))
        self.api_url = api_url
        self.headers = {
            'X-Api-Key': api_key
        }
        self.session = requests.Session()

    def get(self, endpoint):
        try:
            response = self.session.get(
                url='{api_url}/{endpoint}/'.format(api_url=self.api_url, endpoint=endpoint),
                headers=self.headers
            )
            if response.status_code != 200:
                sys.exit('{status_code}: {content}'.format(status_code=response.status_code, content=response.content))
            return response.json()
        except Exception as ex:
            sys.exit(ex)

    def list_clients(self, wid):
        return self.get(endpoint='workspaces/{wid}/clients'.format(wid=wid))

    def list_projects(self, wid):
        return self.get(endpoint='workspaces/{wid}/projects'.format(wid=wid))

    def list_workspaces(self):
        return self.get(endpoint='workspaces')

    def list_users(self, wid):
        return self.get(endpoint='workspaces/{wid}/users'.format(wid=wid))

    def select_workspace(self, name):
        for workspace in self.list_workspaces():
            if workspace['name'] == name:
                return workspace
