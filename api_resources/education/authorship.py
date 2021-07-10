from flask_restful import Resource

from api_resources.base.checkers import jwt_authorizer, lister
from database import Author


class OwnedModuleLister(Resource):  # [POST] /cat/modules/owned/
    @lister(24, jwt_authorizer(Author, "author"))
    def post(self, author: Author, start: int, finish: int):
        return author.get_owned_modules(start, finish)
