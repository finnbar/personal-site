from personalsite import app
from personalsite.database import *
from flask import render_template, session, redirect, url_for, request
from datetime import datetime

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", tags=Tag.query.all(), tag_links=all_links())

@app.route("/blog")
@app.route("/blog/<int:page>")
@app.route("/blog/<string:tag>")
@app.route("/blog/<string:tag>/<int:page>")
def blog(tag=None, page=1):
    posts_per_page = 10
    posts = []
    title = "Posts"
    pagination_url = "/" + str(tag)
    pagination = Post.query.order_by(Post.date.desc()).paginate(page=page, per_page=posts_per_page)
    if not tag:
        posts = pagination.items
        pagination_url = ""
    else:
        tag = Tag.query.filter_by(name=tag.capitalize()).first_or_404()
        pagination = tag.posts.order_by(Post.date.desc()).paginate(page=page, per_page=posts_per_page)
        posts = pagination.items
        title = tag.name.capitalize() + " Posts"
    return render_template("blog.html", blog_title=title, posts=posts, pagination=pagination, pagination_url=pagination_url)

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
        update_post(post, request.form["title"], request.form["content"], request.form["url"])
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:post_id>", methods=["GET"])
def delete(post_id):
    if not "loggedin" in session:
        return redirect(url_for("index"))
    post = Post.query.get_or_404(post_id)
    delete_post(post)
    return redirect(url_for("admin"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "loggedin" in session:
        return redirect(url_for("admin"))
    if request.method == "POST":
        if "password" in request.form:
            if authenticate(request.form["password"]):
                session["loggedin"] = True
                return redirect(url_for("admin"))
        return redirect(url_for("login"))
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    return redirect(url_for("index"))
