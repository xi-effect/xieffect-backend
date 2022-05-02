from flask import jsonify
from flask_jwt_extended import get_jwt, unset_jwt_cookies
from flask_restx import Resource
from flask_restx.reqparse import RequestParser
from itsdangerous import BadSignature

from common import password_parser, Namespace, success_response, TokenBlockList, User
from .invites_db import Invite
# from .emailer import send_generated_email, parse_code

reglog_namespace: Namespace = Namespace("reglog", path="/")
success_response.register_model(reglog_namespace)
add_sets_cookie_response = reglog_namespace.response(*success_response.get_args(),
                                                     headers={"SetCookie": "sets access_token_cookie"})
add_unsets_cookie_response = reglog_namespace.response(*success_response.get_args(),
                                                       headers={"SetCookie": "unsets access_token_cookie"})


@reglog_namespace.route("/reg/")
class UserRegistration(Resource):
    parser: RequestParser = password_parser.copy()
    parser.add_argument("email", required=True, help="Email to be connected to new user's account")
    parser.add_argument("username", required=True, help="Username to be assigned to new user's account")
    parser.add_argument("code", required=True, help="Serialized invite code")

    @add_sets_cookie_response
    @reglog_namespace.with_begin
    @reglog_namespace.argument_parser(parser)
    @reglog_namespace.adds_authorization()
    def post(self, session, email: str, username: str, password: str, code: str):
        """ Creates a new user if email is not used already, logs in automatically """
        try:
            invite = Invite.find_by_code(session, code)
        except BadSignature:
            return {"a": "Malformed code (BadSignature)"}, 400

        if invite is None:
            return {"a": "Invite not found"}, 404
        if invite.limit == invite.accepted:
            return {"a": "Invite code limit exceeded"}
        invite.accepted += 1

        if (user := User.create(session, email=email, username=username, password=password, invite=invite)) is None:
            return {"a": "Email already in use"}
        # send_generated_email(email, "confirm", "registration-email.html")
        return {"a": "Success"}, user


@reglog_namespace.route("/auth/")
class UserLogin(Resource):
    parser: RequestParser = password_parser.copy()
    parser.add_argument("email", required=True, help="User's email")

    @add_sets_cookie_response
    @reglog_namespace.with_begin
    @reglog_namespace.argument_parser(parser)
    @reglog_namespace.adds_authorization()
    def post(self, session, email: str, password: str):
        """ Tries to log in with credentials given """
        if (user := User.find_by_email_address(session, email)) is None:
            return {"a": "User doesn't exist"}

        if User.verify_hash(password, user.password):
            return {"a": "Success"}, user
        return {"a": "Wrong password"}


@reglog_namespace.route("/logout/")
class UserLogout(Resource):
    @add_unsets_cookie_response
    @reglog_namespace.with_begin
    @reglog_namespace.removes_authorization()
    def post(self, session):
        """ Logs the user out, blocks the token """
        TokenBlockList.create(session, jti=get_jwt()["jti"])
        return {"a": True}


@reglog_namespace.route("/go/")
class Test(Resource):
    from api import app

    @add_sets_cookie_response
    @reglog_namespace.with_begin
    @reglog_namespace.adds_authorization()
    def get(self, session):
        """ Localhost-only endpoint for logging in from the docs """
        if not self.app.debug:
            return {"a": False}

        return {"a": True}, User.find_by_id(session, 1)


@reglog_namespace.route("/password-reset/")
class PasswordResetSender(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("email", required=True, help="User's email")

    @reglog_namespace.with_begin
    @reglog_namespace.argument_parser(parser)
    @reglog_namespace.a_response()
    def post(self, session, email: str) -> bool:
        """ First step of resetting password, tries sending a password-reset email by the address given """
        return User.find_by_email_address(session, email) is not None and email != "admin@admin.admin"


@reglog_namespace.route("/password-reset/confirm/")
class PasswordReseter(Resource):
    parser: RequestParser = password_parser.copy()
    parser.add_argument("code", required=True, help="Code sent in the email")

    @reglog_namespace.with_begin
    @reglog_namespace.argument_parser(parser)
    @reglog_namespace.a_response()
    def post(self, session, code: str, password: str) -> str:
        """ Second step of resetting password, sets the new password if code is correct """

        # email = parse_code(code, "pass")
        # if email is None:
        #     return "Code error"

        if (user := User.find_by_email_address(session, email)) is None:
            return "User doesn't exist"
        user.change_password(password)
        return "Success"
