import os

from flask import Flask
from flask_restful import Api
from flask_pymysql import MySQL

from api.resources import DocumentListCreateResource, DocumentRetrieveUpdateDeleteResource, TrendsResource, TopicsResource


pymysql_connect_kwargs = {'user': 'root',
                          'password': '',
                          'host': '127.0.0.1',
                          'database': 'myindex'}


_mysql = None


def get_mysql():
    global _mysql
    return _mysql


def create_app():
    global _mysql
    app = Flask(__name__, instance_relative_config=True)
    app.config['pymysql_kwargs'] = pymysql_connect_kwargs
    app.config['documents_dir'] = os.environ['DOCUMENTS_DIR']
    api = Api(app)

    api.add_resource(DocumentListCreateResource, '/doc')
    api.add_resource(DocumentRetrieveUpdateDeleteResource, '/doc/<string:doc_uuid>')
    api.add_resource(TrendsResource, '/trends/<string:granularity>/<string:term_text>')
    api.add_resource(TopicsResource, '/topics')

    mysql = MySQL()
    mysql.init_app(app)
    _mysql = mysql

    return app
