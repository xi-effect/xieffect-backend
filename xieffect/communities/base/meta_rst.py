from __future__ import annotations

from flask_restx import Resource
from flask_restx.reqparse import RequestParser

from common import Namespace, counter_parser, User
from .meta_db import Community

communities_namespace: Namespace = Namespace("communities-meta", path="/communities/")
community_base = communities_namespace.model("CommunityBase", Community.marshal_models["community-base"])
community_create = communities_namespace.model("CommunityId", Community.marshal_models["community-id"])


@communities_namespace.route("/")
class CommunityCreator(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("name", required=True, type=str)
    parser.add_argument("description", required=False, type=str)

    @communities_namespace.jwt_authorizer(User)
    @communities_namespace.argument_parser(parser)
    @communities_namespace.marshal_with(community_create)
    def post(self, session, user: User, name: str, description: str | None):
        return Community.create(session, name, description, user)


@communities_namespace.route("/index/")
class CommunityLister(Resource):
    @communities_namespace.jwt_authorizer(User)
    @communities_namespace.argument_parser(counter_parser)
    @communities_namespace.lister(20, community_base)
    def post(self, session, user: User, start: int, finish: int):
        return Community.find_by_user(session, user, start, finish - start)
