from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown
from personalsite.secretkey import get_secret_key
from flask_sslify import SSLify

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = get_secret_key()
db = SQLAlchemy(app)
md = Markdown(app)
sslify = SSLify(app)

import personalsite.views
import personalsite.database
