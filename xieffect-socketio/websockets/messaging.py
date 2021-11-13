from flask_socketio import join_room, leave_room
from pydantic import create_model

from library import Session
from library0 import EventGroup, ServerEvent, ClientEvent, DuplexEvent
from setup import user_sessions, app

edit_message_model = create_model("EditMessage", chat_id=(int, ...), message_id=(int, ...))
delete_message_model = create_model("DeleteMessage", __base__=edit_message_model, content=(str, ...))


class Messaging(EventGroup):
    notif: ServerEvent = ServerEvent(create_model("Notif", chat_id=(int, ...), unread=0))
    open_chat: ClientEvent = ClientEvent(create_model("ChatID", chat_id=(int, ...)))
    close_chat: ClientEvent = ClientEvent(create_model("ChatID", chat_id=(int, ...)))

    send_message: DuplexEvent = DuplexEvent.similar(create_model("NewMessage", chat_id=(int, ...), content=(str, ...)))
    edit_message: DuplexEvent = DuplexEvent.similar(edit_message_model)
    delete_message: DuplexEvent = DuplexEvent.similar(delete_message_model)

    def notify_offline(self, session: Session, chat_id: int) -> None:
        user_list = session.get(f"{app.config['host']}/chat-temp/{chat_id}/users/offline/")
        for user_data in user_list.json():
            self.notif.emit("user-" + str(user_data["user-id"]), chat_id=chat_id, unread=user_data["unread"])

    @open_chat.bind
    @user_sessions.with_request_session(use_user_id=True)
    def on_open_chat(self, session: Session, chat_id: int, user_id: int):
        notify_needed = session.post(
            f"{app.config['host']}/chat-temp/{chat_id}/presence/", json={"online": True}).json()["a"]
        join_room(f"chat-{chat_id}")
        if notify_needed:
            self.notif.emit(f"user-{user_id}", chat_id=chat_id, unread=0)

    @close_chat.bind
    @user_sessions.with_request_session()
    def on_close_chat(self, session: Session, chat_id: int):
        session.post(f"{app.config['host']}/chat-temp/{chat_id}/presence/", json={"online": False})
        leave_room(f"chat-{chat_id}")

    @send_message.bind
    @user_sessions.with_request_session()
    def on_send_message(self, session: Session, chat_id: int, content: str):
        session.post(f"{app.config['host']}/chat-temp/{chat_id}/messages/", json={"chat-id": chat_id, "content": content})
        self.send_message.emit(f"chat-{chat_id}", chat_id=chat_id, content=content)
        self.notify_offline(session, chat_id)

    @edit_message.bind
    @user_sessions.with_request_session()
    def on_edit_message(self, session: Session, chat_id: int, message_id: int, content: str):
        session.put(f"{app.config['host']}/chat-temp/{chat_id}/messages/{message_id}/",
                    json={"chat-id": chat_id, "content": content, "message-id": message_id})
        self.edit_message.emit(f"chat-{chat_id}", chat_id=chat_id, message_id=message_id, content=content)
        self.notify_offline(session, chat_id)

    @delete_message.bind
    @user_sessions.with_request_session()
    def on_delete_message(self, session: Session, chat_id: int, message_id: int):
        session.delete(f"{app.config['host']}/chat-temp/{chat_id}/messages/{message_id}/")
        self.delete_message.emit(f"chat-{chat_id}", chat_id=chat_id, message_id=message_id)
        self.notify_offline(session, chat_id)
