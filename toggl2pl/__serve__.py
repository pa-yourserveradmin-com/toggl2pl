from elasticsearch import Elasticsearch
from flask import Blueprint, Flask, abort, make_response, jsonify, request
from toggl2pl import Client
import ast
from datetime import datetime
import logging
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
    :<json string excluded_projects: List of PL projects names to exclude from result.
    :<json string since: The start date in ISO 8601 (`YYYY-MM-DD`) format to pull posts from Toggl.
    :<json string until: The last date in ISO 8601 (`YYYY-MM-DD`) format to pull posts from Toggl.
    :<json string user_key: The Project Laboratory authentication token to use instead of username and password.
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
    try:
        return jsonify(client.posts(since=data['since'], until=data['until']))
    except AssertionError as ae:
        abort(make_response(jsonify(ae.args[0]), 500))


@posts.route(rule='/push', methods=['PUT'])
def push():
    """
    Push single Project Laboratory task information.

    .. :quickref: Push Posts; Push posts into Project Laboratory.

    :reqheader Content-Type: application/json

    :<json string api_token: The Toggl authentication token to use instead of username and password.
    :<json string date: The date in ISO 8601 (`YYYY-MM-DD`) format when work was actually done.
    :<json string description: Relatively short description of the work done as a part of the parent task.
    :<json integer duration: The real amount of minutes spent during work on the task entry.
    :<json string project: The Project Laboratory task parent project name.
    :<json integer rounded: The rounded amount of minutes spent during work on the task entry.
    :<json string task: The Project Laboratory task name.
    :<json string user_key: The Project Laboratory authentication token to use instead of username and password.
    :<json string workspace: The Toggl workspace name (case sensitive) to pull information from.

    :resheader Content-Type: application/json

    :status 200: Request successfully processed and response provided back to client.
    """
    data = request.get_json()
    client = Client(
        api_token=data['api_token'],
        base_url=settings['base_url'],
        log_level=settings['log_level'],
        user_key=data['user_key'],
        verify=settings['verify'],
        workspace=data['workspace'],
    )
    response = jsonify(
        client.add_post(
            date=data['date'],
            description=data['description'],
            minutes=data['rounded'],  # TODO: Start from rounded but provide an ability to optionally post real duration
            project=data['project'],
            task=data['task']
        )
    )
    # TODO: Rewrite Elasticsearch integration to asynchronous job executing outside of the main request context.
    try:
        es = Elasticsearch(hosts=os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch:9200').split(','))
        es.index(
            body={
                'description': data['description'],
                'duration': data['duration'],
                'employee': client.me['email'].split('@')[0].upper(),
                'project': data['project'],
                'rounded': data['rounded'],
                'task': data['task'],
                'timestamp': datetime.strptime(data['date'], '%Y-%m-%d'),
            },
            doc_type='toggl',
            index='toggl',
        )
    except Exception as ex:
        logging.warning(msg=ex)
    return response
