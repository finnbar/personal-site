"""
TODO:
* Implement markdown editing.
"""

from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown
from secretkey import get_secret_key, admin_salt, admin_hash
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = get_secret_key()
db = SQLAlchemy(app)
md = Markdown(app)

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", categories=Category.query.all())

@app.route("/blog")
@app.route("/blog/")
@app.route("/blog/<category>")
def blog(category=None):
    posts = []
    title = "Posts"
    if not category:
        posts = Post.query.order_by(Post.date.desc())
    else:
        category = Category.query.filter_by(name=category.capitalize()).first_or_404()
        posts = category.posts.order_by(Post.date.desc())
        title = category.name.capitalize() + " Posts"
    return render_template("blog.html", blog_title=title, posts=posts, show_category=(category==None))

@app.route("/admin")
@app.route("/admin/")
def admin():
    if not "loggedin" in session:
        return redirect(url_for("login"))
    else:
        return render_template("admin.html", posts=Post.query.order_by(Post.date.desc()))

@app.route("/admin/new")
@app.route("/admin/new/")
@app.route("/admin/<int:post_id>")
def edit(post_id=None):
    if not "loggedin" in session:
        return redirect(url_for("login"))
    if post_id == None:
        return render_template("edit.html", post=EmptyPost())
    else:
        post = Post.query.get_or_404(post_id)
        return render_template("edit.html", post=post)

@app.route("/admin/update/<int:post_id>", methods=["POST"])
def update(post_id):
    if post_id == 0:
        new_post(request.form["title"], request.form["content"], datetime.now(), request.form["url"], request.form["category"])
    else:
        # Update Post
        post = Post.query.get_or_404(post_id)
        post.title = request.form["title"]
        post.content = request.form["content"]
        post.mainurl = request.form["url"]
        db.session.commit()
    return redirect(url_for("admin"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "loggedin" in session:
        return redirect(url_for("admin"))
    if request.method == "POST":
        print("was POST")
        if "password" in request.form:
            print(request.form["password"])
            if authenticate(request.form["password"]):
                print("was correct")
                session["loggedin"] = True
                return redirect(url_for("admin"))
        return redirect(url_for("login"))
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    return redirect(url_for("index"))

# The reason I'm doing this rather than introducing a full user database is that I only ever want there to be one user (me) editing posts. This isn't meant to scale at all.
def authenticate(password):
    salt = admin_salt().encode("utf-8")
    hashed = admin_hash()
    encoded = password.encode("utf-8")
    return hashlib.sha256(encoded + salt).hexdigest() == hashed

# Post Database:

def new_post(title, content, date, mainurl, category_name):
    # Find category, if not there, make it.
    category = Category.query.filter_by(name=category_name.capitalize()).first()
    if not category:
        category = Category(category_name.capitalize())
        db.session.add(category)
    post = Post(title, content, date, mainurl, category)
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

class EmptyPost():
    id = 0
    title = "A New Post"
    content = ""
    mainurl = ""

    def __init__(self):
        pass
