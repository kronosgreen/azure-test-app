from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_cors import CORS

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine

from bokeh.plotting import figure, ColumnDataSource
from bokeh.embed import server_document
from bokeh.server.server import Server
from tornado.ioloop import IOLoop

from os.path import join
from threading import Thread

import pandas as pd
import socket

app = Flask(__name__)
CORS(app)

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

print("Connecting to database...")
db_engine = create_engine(connection_url)

with db_engine.connect() as conn:
    print("Getting data...")
    df = pd.read_sql('SELECT * FROM annual_working_hours_per_worker', conn)


def bkapp(doc):
    source = ColumnDataSource(df)

    fig = figure(width=800, name='working_hours')
    fig.scatter(x='Year', y='Average annual working hours per worker', source=source)

    doc.add_root(fig)


@app.route('/', methods=['GET'])
def bkapp_page():
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        print("Hostname :  %s" % host_name)
        print("IP : %s" % host_ip)
    except Exception as ex:
        print(ex)
        print("Unable to get Hostname and IP")

    script = server_document('http://127.0.0.1:5006/bkapp')
    return render_template("index.html", script=script)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(join(app.root_path, 'static/images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/bkapp': bkapp}, io_loop=IOLoop(), allow_websocket_origin=[
                    "127.0.0.1:5000", "localhost:5000", "localhost:5006",
                    "dashboard-flask-demo.azurewebsites.net"])
    server.start()
    server.io_loop.start()


print("Spinning up Bokeh worker")
Thread(target=bk_worker).start()

print("Running app...")
if __name__ == '__main__':
    app.run()
