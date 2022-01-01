from typing import Union

from flask_restx import Resource
from flask_restx.reqparse import RequestParser

from componets import Namespace, counter_parser
from users import User
from .metabase import Community

communities_namespace: Namespace = Namespace("communities-meta", path="/communities/")
community_base = communities_namespace.model("CommunityBase", Community.marshal_models["community-base"])


@communities_namespace.route("/")
class CommunityCreator(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("name", required=True, type=str)
    parser.add_argument("description", required=False, type=str)

    @communities_namespace.jwt_authorizer(User)
    @communities_namespace.argument_parser(parser)
    @communities_namespace.a_response()
    def post(self, session, user: User, name: str, description: Union[str, None]) -> bool:
        Community.create(session, name, description, user)  # community =
        return True  # temp


@communities_namespace.route("/index/")
class CommunityLister(Resource):
    @communities_namespace.jwt_authorizer(User)
    @communities_namespace.argument_parser(counter_parser)
    @communities_namespace.lister(20, community_base)
    def post(self, session, user: User, start: int, finish: int):
        return Community.find_by_user(session, user, start, finish - start)
