from os import remove
from typing import Type, List

from flask import request, send_file
from flask_restful import Resource

from componets import jwt_authorizer, lister
from keeper import CATFile, Page
from authorship.user_roles import Author


def file_getter(function):
    @jwt_authorizer(Author, "author")
    def get_file_or_type(file_type: str, author: Author, *args, **kwargs):
        result: Type[CATFile]
        if file_type == "courses":
            result = None
        elif file_type == "pages":
            result = Page
        else:
            return {"a": f"File type '{file_type}' is not supported"}, 406

        if "file_id" in kwargs.keys():
            file: result = result.find_by_id(kwargs.pop("file_id"))
            if file.owner.id != author.id:
                return {"a": "Access denied"}, 403
            return function(file=file, *args, **kwargs)
        else:
            return function(file_type=result, *args, **kwargs)

    return get_file_or_type


class FileLister(Resource):  # [POST] /wip/<file_type>/index/
    @lister(12, file_getter)
    def post(self, file_type: Type[CATFile], author: Author, start: int, finish: int):
        file_list: List[file_type] = file_type.find_by_owner(author, start, finish - start)
        return list(map(lambda x: x.to_json(), file_list))


class FileProcessor(Resource):  # [GET|PUT|DELETE] /wip/<file_type>/<int:file_id>/
    @file_getter
    def get(self, file: CATFile):
        return send_file(file.get_link())

    @file_getter
    def put(self, file: CATFile):
        with open(file.get_link(), "wb") as f:
            f.write(request.data)
        return {"a": True}

    @file_getter
    def delete(self, file: CATFile):
        remove(file.get_link())
        return {"a": True}


class FileCreator(Resource):  # [POST] /wip/<file_type>/
    @file_getter
    def post(self, author: Author, file_type: Type[CATFile]):
        pass
