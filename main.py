"""
TODO:
* Make base templates.
* Sanitise content to remove non-local scripts and images.
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from secretkey import get_secret_key, admin
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = get_secret_key()
db = SQLAlchemy(app)

@app.route("/")
def index():
    return render_template("index.html", categories=Category.query.all())

@app.route("/blog")
@app.route("/blog/")
@app.route("/blog/<category>")
def blog(category=None):
    posts = []
    title = "Posts"
    if not category:
        posts = Post.query.order_by(Post.date)
    else:
        category = Category.query.filter_by(name=category.capitalize()).first_or_404()
        posts = category.posts.order_by(Post.date)
        title = category.name.capitalize() + " Posts"
    return render_template("blog.html", blog_title=title, posts=posts, show_category=(category==None))

# The reason I'm doing this rather than introducing a full user database is that I only ever want there to be one user (me) editing posts. This isn't meant to scale at all.
def authenticate(password):
    details = admin()
    return hashlib.sha256(password.encode("utf-8") + details["salt"]).hexdigest() == details["hashed"]

# Post Database:

def new_post(title, content, date, mainurl, category_name, imageurls=[]):
    # Find category, if not there, make it.
    category = Category.query.filter_by(name=category_name.capitalize()).first()
    if not category:
        category = Category(category_name.capitalize())
        db.session.add(category)
    post = Post(title, content, date, mainurl, category)
    db.session.add(post)
    for url in imageurls:
        new_image = Image(url, post)
        db.session.add(post)
    db.session.commit()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))

    def __init__(self, name):
        self.name = name

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime)
    mainurl = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, title, content, date, mainurl, category):
        self.title = title
        self.content = content
        self.date = date
        self.mainurl = mainurl
        self.category = category

# Will not be implemented for a while. Needs to work with Flask-Upload and the Admin interface.
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', backref=db.backref('images', lazy='dynamic'))
    url = db.String(100)

    def __init__(self, url, post):
        self.url = url
        self.post = post
