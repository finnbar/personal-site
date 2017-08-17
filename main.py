"""
TODO:
* Make base templates.
* Configure login and post storage for SQLAlchemy.
* Sanitise content to remove non-local scripts, images.
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from secretkey import get_secret_key, admin
import hashlib

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = get_secret_key()
db = SQLAlchemy(app)

@app.route("/")
def index():
    return render_template("index.html")

# The reason I'm doing this rather than introducing a full user database is that I only ever want there to be one user (me) editing posts. This isn't meant to scale at all.
def authenticate(password):
    details = admin()
    return hashlib.sha256(password.encode("utf-8") + details["salt"]).hexdigest() == details["hashed"]

# Post Database:
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    content = db.Column(db.Text())
    date = db.Column(db.String(100))
    mainurlname = db.Column(db.String(80))
    mainurl = db.Column(db.String(100))
    tags = db.relationship('Tags', backref='post', lazy='dynamic')
    images = db.relationship('Image', backref='post', lazy='dynamic')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    name = db.String(40)

# Will not be implemented for a while. Needs to work with Flask-Upload and the Admin interface.
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    url = db.String(100)
