from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

from os.path import join

app = Flask(__name__)


@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(join(app.root_path, 'static/images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run()
