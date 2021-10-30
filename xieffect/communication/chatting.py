from flask_restx import Resource, Model
from flask_restx.fields import Integer
from flask_restx.reqparse import RequestParser

from componets import counter_parser, ResponseDoc
from users import User
from .entities import UserToChat, Chat, Message, ChatRole
from .helpers import ChatNamespace

chats_namespace = ChatNamespace("chats", path="/chats/")

chat_meta_parser: RequestParser = RequestParser()
chat_meta_parser.add_argument("name", str, required=True)

chat_meta_view = chats_namespace.model("ChatMeta", Chat.marshal_models["chat-meta"])
chat_full_view = chats_namespace.model("ChatFull", Chat.marshal_models["chat-full"])
message_view = chats_namespace.model("Message", Message.marshal_models["message-full"])


@chats_namespace.route("/index/")
class ChatLister(Resource):
    @chats_namespace.jwt_authorizer(User, use_session=False)
    @chats_namespace.lister(20, chat_meta_view)
    def post(self, user: User, start: int, finish: int):  # dunno how to pagination yet
        """ Get all chats with metadata """
        return user.chats[start:finish - 1]


@chats_namespace.route("/<int:chat_id>/")
class ChatProcessor(Resource):
    @chats_namespace.search_user_to_chat(use_chat=True)
    @chats_namespace.marshal_with(chat_full_view, skip_none=True)
    def get(self, chat: Chat):
        """ Returns chat's full info + user's role """
        return chat  # add user's role & user count!!!

    # @chats_namespace.jwt_authorizer(User)
    # @chats_namespace.database_searcher(Chat)
    # @chats_namespace.argument_parser(chat_meta_parser)
    # @chats_namespace.a_response()
    # def post(self, user: User, chat: Chat) -> None:
    #     """ User joins a chat [???] """
    #     pass

    @chats_namespace.search_user_to_chat(use_user_to_chat=True, use_session=True)
    @chats_namespace.a_response()
    def delete(self, session, user_to_chat: UserToChat) -> None:
        """ Used for quitting the chat by the logged-in user """
        user_to_chat.delete(session)


@chats_namespace.route("/<int:chat_id>/message-history/")
class MessageLister(Resource):
    @chats_namespace.search_user_to_chat(use_chat=True)
    @chats_namespace.argument_parser(counter_parser)
    @chats_namespace.lister(50, message_view)
    def post(self, chat: Chat, start: int, finish: int) -> list[Message]:
        """ Lists chat's messages (new on top) """
        return chat.messages[start:finish + 1]


@chats_namespace.route("/")
class ChatAdder(Resource):
    @chats_namespace.doc_responses(ResponseDoc(model=Model("ID Response", {"id": Integer})))
    @chats_namespace.jwt_authorizer(User)
    @chats_namespace.argument_parser(chat_meta_parser)
    def post(self, session, name: str, user: User) -> dict[str, int]:
        """ Creates a new chat and returns its id """
        return {"id": Chat.create(session, name, user).id}


@chats_namespace.route("/<int:chat_id>/manage/")
class ChatManager(Resource):
    @chats_namespace.search_user_to_chat(min_role=ChatRole.ADMIN, use_chat=True)
    @chats_namespace.argument_parser(chat_meta_parser)
    @chats_namespace.a_response()
    def put(self, chat: Chat) -> None:
        """ Changes some of chat's metadata (chat admins only) """
        pass

    @chats_namespace.search_user_to_chat(min_role=ChatRole.OWNER, use_chat=True)
    @chats_namespace.a_response()
    def delete(self, chat: Chat) -> None:
        """ Deletes a chat (chat admins only) """
        pass


@chats_namespace.route("/<int:chat_id>/users/<int:user_id>/")
class ChatUserManager(Resource):
    @chats_namespace.search_user_to_chat(min_role=ChatRole.ADMIN, use_chat=True)
    @chats_namespace.database_searcher(User, result_field_name="target")
    @chats_namespace.a_response()
    def post(self, chat: Chat, target: User) -> None:
        """ Adds (invites?) a user to the chat """
        pass

    @chats_namespace.search_user_to_chat(min_role=ChatRole.ADMIN, use_chat=True)
    @chats_namespace.database_searcher(User, result_field_name="target")
    @chats_namespace.a_response()
    def put(self, chat: Chat, target: User) -> None:
        """ Changes user's role """
        pass

    @chats_namespace.search_user_to_chat(min_role=ChatRole.ADMIN, use_chat=True)
    @chats_namespace.database_searcher(User, result_field_name="target")
    @chats_namespace.a_response()
    def delete(self, chat: Chat, target: User) -> None:
        """ Removes a user from the chat """
        pass
