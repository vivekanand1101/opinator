from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('opinator.config')
db = SQLAlchemy(app)

from opinator.app import views, models
