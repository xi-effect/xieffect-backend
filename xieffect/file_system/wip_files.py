from typing import Type

from flask import request, send_file
from flask_restful import Resource

from authorship import Author
from componets import jwt_authorizer, lister
from .keeper import CATFile, JSONFile, WIPModule, WIPPage, Image


def file_getter(function):
    @jwt_authorizer(Author, "author")
    def get_file_or_type(file_type: str, author: Author, *args, **kwargs):
        result: Type[CATFile]
        if file_type == "modules":
            result = WIPModule
        elif file_type == "pages":
            result = WIPPage
        elif file_type == "images":
            result = Image
        else:
            return {"a": f"File type '{file_type}' is not supported"}, 400

        if "file_id" in kwargs.keys():
            file: result = result.find_by_id(kwargs.pop("file_id"))
            if file.owner.id != author.id:
                return {"a": "Access denied"}, 403
            return function(file=file, *args, **kwargs)
        else:
            return function(file_type=result, *args, **kwargs)

    return get_file_or_type


class FileLister(Resource):  # [POST] /wip/<file_type>/index/
    @file_getter
    @lister(12)
    def post(self, file_type: Type[CATFile], author: Author, start: int, finish: int):
        if WIPModule not in file_type.mro():
            return {"a": f"File type '{file_type}' is not supported"}, 400
        return [x.get_metadata() for x in file_type.find_by_owner(author, start, finish - start)]


class FileCreator(Resource):  # [POST] /wip/<file_type>/
    @file_getter
    def post(self, author: Author, file_type: Type[CATFile]):
        if isinstance(file_type, JSONFile):
            file_type.create_from_json(author, request.get_json())
        else:
            file_type.create_with_file(author, request.get_data())
        return {"a": True}


class FileProcessor(Resource):  # [GET|PUT|DELETE] /wip/<file_type>/<int:file_id>/
    @file_getter
    def get(self, file: CATFile):
        return send_file(file.get_link())

    @file_getter
    def put(self, file: CATFile):
        if isinstance(file, JSONFile):
            file.update_json(request.get_json())
        else:
            file.update(request.get_data())
        return {"a": True}

    @file_getter
    def delete(self, file: CATFile):
        file.delete()
        return {"a": True}
