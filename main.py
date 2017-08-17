from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from secretkey import get_secret_key

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db" # NEED TO CHANGE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = get_secret_key()
db = SQLAlchemy(app)

@app.route("/")
def index():
    return "Hello World!"
