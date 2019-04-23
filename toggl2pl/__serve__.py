from flask import Blueprint, Flask, request, jsonify
from toggl2pl import Client
import ast
import os


settings = {
    'base_url': os.getenv('BASE_URL', 'https://pl.itcraft.co/api/client-v1'),
    'log_level': os.getenv('LOG_LEVEL', 'info'),
    'verify': ast.literal_eval(os.getenv('SSL_VERIFY', 'true').lower().title())
}


def create_app():
    """
    Create a new instance of Flask application to start serving requests.

    :return: Instance of :class:`flask.Flask`.
    """
    app = Flask(__name__)
    app.register_blueprint(blueprint=posts)
    return app


posts = Blueprint('posts', __name__, url_prefix='/posts')


@posts.route(rule='/pull', methods=['GET'])
def pull():
    """
    Pull list of Toggl posts in period between specified since and until dates.

    .. :quickref: Pull Posts; Pull posts from Toggl and send to client.

    :reqheader Content-Type: application/json

    :<json string api_token: The Toggl authentication token to use instead of username and password.
    :<jsoon string excluded_projects: List of PL projects names to exclude from result.
    :<json string since: The *first* date in ISO 8601 (`YYYY-MM-DD`) format to pull posts from Toggl.
    :<json string until: The *last* date in ISO 8601 (`YYYY-MM-DD`) format to pull posts from Toggl.
    :<jsoon string user_key: The Project Laboratory authentication token to use instead of username and password.
    :<json string workspace: The Toggl workspace name (case sensitive) to pull information from.

    :resheader Content-Type: application/json

    :status 200: Request successfully processed and response provided back to client.
    """
    data = request.get_json()
    client = Client(
        api_token=data['api_token'],
        base_url=settings['base_url'],
        excluded_projects=data['excluded_projects'],
        log_level=settings['log_level'],
        user_key=data['user_key'],
        verify=settings['verify'],
        workspace=data['workspace'],
    )
    return jsonify(client.posts(since=data['since'], until=data['until']))


@posts.route(rule='/push', methods=['PUT'])
def push():
    pass

