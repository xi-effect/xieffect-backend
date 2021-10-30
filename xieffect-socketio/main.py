from datetime import timedelta
from os import getenv

from dotenv import load_dotenv
from flask import Flask, send_file  # , request
from flask_socketio import SocketIO, emit
from flask_jwt_extended import JWTManager  # , get_jwt_identity

load_dotenv("../.env")

app = Flask(__name__)

# JWT config:
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_COOKIE_SAMESITE"] = "None"
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=72)
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access"]
app.config["JWT_SECRET_KEY"] = getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)

socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def index():
    return send_file("index.html")


@socketio.on('connect')
def connect():
    pass


@socketio.on("message")
def handle_message(data):
    # verify_jwt_in_request()
    # print(request.headers)
    # print(get_jwt_identity())
    # print(data)
    emit("new_message", data, broadcast=True)


if __name__ == "__main__":
    # send_discord_message(WebhookURLs.HEROKU, "Heroku may be online")
    socketio.run(app, port=5050, debug=True)