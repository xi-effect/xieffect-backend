from enum import Enum

from main import db
from componets import Identifiable
from authorship import Author


class Locations(Enum):
    SERVER = 0

    def to_link(self, file_type: str, file_id: int) -> str:
        result: str = ""
        if self == Locations.SERVER:
            result = f"/files/tfs/{file_type}/{file_id}/"

        return result


class CATFile(db.Model, Identifiable):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False,
                      default=0)  # test-only
    location = db.Column(db.Integer, nullable=True)

    @classmethod
    def find_by_id(cls, entry_id: int):
        return cls.query.filter_by(id=entry_id).first()

    @classmethod
    def find_by_owner(cls, owner: Author, start: int, limit: int) -> list:
        return cls.query.filter_by(owner=owner).offset(start).limit(limit).all()

    def get_link(self) -> str:
        return Locations(self.location).to_link(self.__tablename__, self.id)

    def to_json(self) -> str:
        raise NotImplementedError


class Page(CATFile):
    __tablename__ = "pages"
    not_found_text = "Page not found"

    tags = db.Column(db.String(100), nullable=False)
    reusable = db.Column(db.Boolean, nullable=False)
    published = db.Column(db.Boolean, nullable=False)

    def to_json(self) -> str:
        pass


class WIPModule(CATFile):
    __tablename__ = "pages"
    not_found_text = "Module not found"

    pass

    def to_json(self) -> str:
        pass
