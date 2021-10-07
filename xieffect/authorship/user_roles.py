from sqlalchemy import Column, select
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, Boolean

from componets import UserRole
from componets.checkers import first_or_none
from main import Base, Session


class Author(Base, UserRole):
    __tablename__ = "authors"
    not_found_text = "Author does not exist"

    id = Column(Integer, primary_key=True)
    pseudonym = Column(String(100), nullable=False)
    banned = Column(Boolean, nullable=False, default=False)
    last_image_id = Column(Integer, nullable=False, default=0)

    modules = relationship("Module", backref="authors")

    @classmethod
    def create(cls, session: Session, user):  # User class
        new_entry = cls(id=user.id, pseudonym=user.username)
        session.add(new_entry)
        return new_entry

    @classmethod
    def find_by_id(cls, session: Session, entry_id: int, include_banned: bool = False):
        return first_or_none(session.execute(
            select(cls).where(cls.id == entry_id) if include_banned
            else select(cls).where(cls.id == entry_id, cls.banned == False)
        ))

    @classmethod
    def find_or_create(cls, session: Session, user):  # User class
        if (author := cls.find_by_id(session, user.id, True)) is None:
            author = cls.create(session, user)
        return author

    @classmethod
    def initialize(cls, session: Session, user) -> bool:  # User class
        author = cls.find_by_id(session, user)
        return not author.banned

    def get_next_image_id(self):  # auto-commit
        self.last_image_id += 1
        return self.last_image_id


class Moderator(Base, UserRole):
    __tablename__ = "moderators"
    not_found_text = "Permission denied"

    id = Column(Integer, primary_key=True)

    @classmethod
    def find_by_id(cls, session: Session, entry_id: int):
        return first_or_none(session.execute(select(cls).where(cls.id == entry_id)))

    @classmethod
    def create(cls, session: Session, user_id: int) -> bool:
        if cls.find_by_id(session, user_id):
            return False
        new_entry = cls(id=user_id)
        session.add(new_entry)
        return True
