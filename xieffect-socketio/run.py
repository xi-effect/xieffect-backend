from flask_restx import Api

from setup import socketio, app
from websockets import TestNamespace, MessagesNamespace
from temp_api import pass_through_namespace, reglog_namespace, static_namespace

api = Api(app, doc="/doc/")
api.add_namespace(static_namespace)
api.add_namespace(reglog_namespace)
api.add_namespace(pass_through_namespace)

socketio.on_namespace(TestNamespace("/test"))
socketio.on_namespace(MessagesNamespace("/"))

if __name__ == "__main__":
    socketio.run(app, port=5050, debug=True)