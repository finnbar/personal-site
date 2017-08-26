from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown
from secretkey import get_secret_key, admin_salt, admin_hash
from datetime import datetime
import hashlib, re

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = get_secret_key()
db = SQLAlchemy(app)
md = Markdown(app)

tag_split = re.compile("#(\w+)")

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", tags=Tag.query.all())

@app.route("/blog")
@app.route("/blog/")
@app.route("/blog/<tag>")
def blog(tag=None):
    posts = []
    title = "Posts"
    if not tag:
        posts = Post.query.order_by(Post.date.desc())
    else:
        tag = Tag.query.filter_by(name=tag.capitalize()).first_or_404()
        posts = tag.posts.order_by(Post.date.desc())
        title = tag.name.capitalize() + " Posts"
    return render_template("blog.html", blog_title=title, posts=posts)

@app.route("/post/<int:post_id>")
def post(post_id=None):
    if post_id == None:
        return redirect(url_for("index"))
    else:
        post = Post.query.get_or_404(post_id)
        return render_template("post.html", post=post)

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
    if not "loggedin" in session:
        return redirect(url_for("index"))
    if post_id == 0:
        new_post(request.form["title"], request.form["content"], datetime.now(), request.form["url"], request.form["tags"])
    else:
        # Update Post
        post = Post.query.get_or_404(post_id)
        post.title = request.form["title"]
        post.content = request.form["content"]
        post.mainurl = request.form["url"]
        db.session.commit()
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:post_id>", methods=["GET"])
def delete(post_id):
    if not "loggedin" in session:
        return redirect(url_for("index"))
    post = Post.query.get_or_404(post_id)
    for tag in post.tags:
        if len(tag.posts) == 1:
            db.session.delete(tag)
    db.session.delete(post)
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

def new_post(title, content, date, mainurl, tag_string):
    post = Post(title, content, date, mainurl)
    # Find tag, if not there, make it.
    for tag in tag_split.findall(tag_string):
        tag_object = Tag.query.filter_by(name=tag.capitalize()).first()
        if not tag_object:
            tag_object = Tag(tag.capitalize())
            db.session.add(tag_object)
        post.tags.append(tag_object)
    db.session.add(post)
    db.session.commit()

tags = db.Table('tags',
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
        db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime)
    mainurl = db.Column(db.String(100))
    tags = db.relationship('Tag', secondary=tags, backref=db.backref('posts', lazy='dynamic'))

    def __init__(self, title, content, date, mainurl):
        self.title = title
        self.content = content
        self.date = date
        self.mainurl = mainurl

    def taglist(self):
        tag_string = ''
        for tag in self.tags:
            tag_string += tag.name + ', '
        return tag_string[:-2]

    def tag_names(self):
        return list(map(lambda tag: tag.name, self.tags))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    #posts = db.relationship('Post', secondary=tags, backref=db.backref('tags', lazy='dynamic'))

    def __init__(self, name):
        self.name = name

    def post_count(self):
        return len(self.posts.all())

class EmptyPost():
    id = 0
    title = "A New Post"
    content = ""
    mainurl = ""

    def __init__(self):
        pass
