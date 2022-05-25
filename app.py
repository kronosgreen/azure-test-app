from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from bokeh.plotting import figure, ColumnDataSource
from bokeh.embed import server_document
from bokeh.server.server import Server
from bokeh.io import curdoc
from tornado.ioloop import IOLoop

from os.path import join
from threading import Thread

import pandas as pd

app = Flask(__name__)

vault_url = 'https://dashboard-test-keys.vault.azure.net/'
credential = DefaultAzureCredential()
client = SecretClient(vault_url=vault_url, credential=credential)

engine = 'postgresql+psycopg2'
user = client.get_secret('test-db-user').value
password = client.get_secret('test-db-pass').value
host = client.get_secret('test-db-host').value
db = 'test-db'

connection_url = '%s://%s:%s@%s/%s?sslmode=require' % \
    (engine, user, urlquote(password), host, db)

db_engine = create_engine(connection_url)
with db_engine.connect() as conn:
    df = pd.read_sql('SELECT * FROM annual_working_hours_per_worker', conn)


def bkapp(doc):
    source = ColumnDataSource(df)

    fig = figure(width=800, name='working_hours')
    fig.scatter(x='Year', y='Average annual working hours per worker', source=source)

    doc.add_root(fig)


@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template("index.html", script=script)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(join(app.root_path, 'static/images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/bkapp': bkapp}, io_loop=IOLoop(), allow_websocket_origin=["127.0.0.1:5000"])
    server.start()
    server.io_loop.start()


Thread(target=bk_worker).start()

if __name__ == '__main__':
    app.run()
