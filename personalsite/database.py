from personalsite import db
from personalsite.secretkey import admin_salt, admin_hash
import hashlib, re

tag_split = re.compile("#(\w+)")

# The reason I'm doing this rather than introducing a full user database is that I only ever want there to be one user (me) editing posts. This isn't meant to scale at all.
def authenticate(password):
    salt = admin_salt().encode("utf-8")
    hashed = admin_hash()
    encoded = password.encode("utf-8")
    return hashlib.sha256(encoded + salt).hexdigest() == hashed

# Posts Functionality:

def new_post(title, content, date, mainurl, tag_string):
    post = Post(title, content, date, mainurl)
    post.tags = add_tags(tag_string)
    db.session.add(post)
    db.session.commit()

def delete_post(post):
    remove_tags(post)
    db.session.delete(post)
    db.session.commit()

def update_post(post, title, content, url):
    post.title = title
    post.content = content
    post.url = url
    db.session.commit()

def link_tag(source, target):
    existing_link = find_link(source, target)
    if existing_link is None:
        link = LinkedTag(source, target)
        db.session.add(link)
    else:
        existing_link.increment()
    db.session.commit()

def unlink_tag(source, target):
    existing_link = find_link(source, target)
    if not existing_link is None:
        existing_link.decrement()
        db.session.commit()

def find_link(source, target):
    existing_link = LinkedTag.query.filter_by(source=source, target=target).first()
    if existing_link is None:
        existing_link = LinkedTag.query.filter_by(source=target, target=source).first()
    return existing_link

def all_links():
    links_data = []
    for link in LinkedTag.query.all():
        links_data.append({"source": link.source, "target": link.target, "value": link.value})
    return links_data

def remove_tags(post):
    for tag in post.tags:
        if len(tag.posts) == 1:
            for link in LinkedTag.query.filter_by(source=tag.id):
                db.session.delete(link)
            for link in LinkedTag.query.filter_by(target=tag.id):
                db.session.delete(link)
            db.session.delete(tag)

def add_tags(tag_string):
    tags = tag_split.findall(tag_string)
    tag_objects = []
    for tag in tags:
        # See if the tag exists already:
        tag_object = Tag.query.filter_by(name=tag.capitalize()).first()
        if not tag_object:
            # If not, create it!
            tag_object = Tag(tag.capitalize())
            db.session.add(tag_object)
        db.session.commit()

        # For all other tags we've encountered:
        for linked_tag in tag_objects:
            # Link it to this one.
            link_tag(tag_object.id, linked_tag.id)
        tag_objects.append(tag_object)
    return tag_objects

tags = db.Table("tags",
        db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
        db.Column("post_id", db.Integer, db.ForeignKey("post.id")),
)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime)
    mainurl = db.Column(db.String(100))
    tags = db.relationship("Tag", secondary=tags, backref=db.backref("posts", lazy="dynamic"))

    def __init__(self, title, content, date, mainurl):
        self.title = title
        self.content = content
        self.date = date
        self.mainurl = mainurl

    def tag_names(self):
        return list(map(lambda tag: tag.name, self.tags))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    def __init__(self, name):
        self.name = name

    def post_count(self):
        return len(self.posts.all())

class LinkedTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Integer, db.ForeignKey("tag.id"))
    target = db.Column(db.Integer, db.ForeignKey("tag.id"))
    value = db.Column(db.Integer)

    def __init__(self, s, t):
        self.source = s
        self.target = t
        self.value = 1

    def increment(self):
        self.value += 1

    def decrement(self):
        self.value -= 1

class EmptyPost():
    id = 0
    title = "A New Post"
    content = ""
    mainurl = ""

    def __init__(self):
        pass
