from flask import Flask
from flask_pymysql import MySQL
from flask_restful import Api

from api.resources import (
    DocumentListCreateResource,
    DocumentRetrieveUpdateDeleteResource,
    TrendsResource,
    TopicsResource,
    RPCResource,
)
from config import PYMYSQL_CONNECT_ARGS, DOCUMENTS_DIR

_mysql = None


def get_mysql():
    global _mysql
    return _mysql


def create_app():
    global _mysql
    app = Flask(__name__, instance_relative_config=True)
    app.config['pymysql_kwargs'] = PYMYSQL_CONNECT_ARGS
    app.config['documents_dir'] = DOCUMENTS_DIR
    api = Api(app)

    api.add_resource(DocumentListCreateResource, '/doc')
    api.add_resource(DocumentRetrieveUpdateDeleteResource, '/doc/<string:doc_uuid>')
    api.add_resource(TrendsResource, '/trends/<string:granularity>/<string:term_text>')
    api.add_resource(TopicsResource, '/topics')
    api.add_resource(RPCResource, '/rpc/<string:function>')

    mysql = MySQL()
    mysql.init_app(app)
    _mysql = mysql

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        response.headers.add('Referrer-Policy', 'no-referrer')
        return response

    return app
