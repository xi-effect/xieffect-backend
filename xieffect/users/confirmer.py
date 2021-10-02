from flask_restful import Resource
from flask_restful.reqparse import RequestParser

from componets import argument_parser, with_session
from users.database import User
# from users.emailer import send_generated_email, parse_code


class EmailSender(Resource):  # [POST] /email/<email>/
    @with_session
    def post(self, session, email: str):
        user: User = User.find_by_email_address(session, email)
        if user is None:
            return {"a": User.not_found_text}, 404
        if user.email_confirmed:
            return {"a": "Confirmed"}
        # if timeout
        #     return {"a": "Too fast"}

        # send_generated_email(email, "confirm", "registration-email.html")
        return {"a": "Success"}


class EmailConfirm(Resource):  # [POST] /email-confirm/
    parser: RequestParser = RequestParser()
    parser.add_argument("code", required=True)

    @with_session
    @argument_parser(parser, "code")
    def post(self, code: str):
        # email = parse_code(code, "confirm")
        # if email is None:
        #     return {"a": "Code error"}

        user: User = User.find_by_email_address(session, email)
        if user is None:
            return {"a": User.not_found_text}, 404

        user.confirm_email()
        return {"a": "Success"}