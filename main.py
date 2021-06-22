from os import urandom
from json import load
from random import randint
from typing import Dict
from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Version control:
versions: Dict[str, str] = load(open("files/versions.json"))

app: Flask = Flask(__name__)

# Basic config:
app.config["SECRET_KEY"] = urandom(randint(32, 64))
app.config["SECURITY_PASSWORD_SALT"] = urandom(randint(32, 64))
app.config["PROPAGATE_EXCEPTIONS"] = True

# JWT config:
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_COOKIE_SAMESITE"] = "None"
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=72)
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access"]
app.config["JWT_SECRET_KEY"] = urandom(randint(32, 64))

app.config["MAIL_USERNAME"] = "xieffect.edu@gmail.com"

# CORS config:
CORS(app, supports_credentials=True)  # , resources={r"/*": {"origins": "https://xieffect.vercel.app"}})

# Database config:
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database/app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config[""] =

db: SQLAlchemy = SQLAlchemy(app)