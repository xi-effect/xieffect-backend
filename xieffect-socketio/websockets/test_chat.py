from flask_socketio import emit, Namespace, join_room, rooms

from temp_api.broadcast import room_broadcast


class TestNamespace(Namespace):
    def on_connect(self, *_):
        join_room("chat")
        print(rooms())
        room_broadcast("new_message", "hey", "chat", "/test")

    def on_message(self, data):
        # verify_jwt_in_request()
        # print(request.headers)
        # print(get_jwt_identity())
        # print(data)
        room_broadcast("new_message", data, "chat", "/test")
