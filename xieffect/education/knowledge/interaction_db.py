from __future__ import annotations

from flask_fullstack import PydanticModel
from sqlalchemy import Column, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, Float, JSON

from common import User, Base, db
from ._base_session import BaseModuleSession  # noqa: WPS436


class ModuleProgressSession(BaseModuleSession):
    __tablename__ = "standard_module_sessions"
    progress = Column(Integer, nullable=True)
    theory_level = Column(Float, nullable=True)  # temp disabled for theory blocks

    # TODO remove the noqa
    def get_theory_level(self) -> float | None:  # noqa: WPS615
        if self.theory_level is None:
            return None
        return (
            User.find_by_id(self.user_id).theory_level * 0.2 + self.theory_level * 0.8
        )


class TestModuleSession(BaseModuleSession):
    __tablename__ = "test_module_sessions"
    not_found_text = "Test session not found"
    points = relationship("TestPointSession", cascade="all, delete")

    def create_point_session(
        self,
        point_id: int,
        module,
    ) -> TestPointSession:
        page_id = module.execute_point(point_id)
        new_entry = TestPointSession(page_id=page_id, point_id=point_id)
        self.points.append(new_entry)
        db.session.flush()
        return new_entry

    def find_point_session(self, point_id: int) -> TestPointSession | None:
        return TestPointSession.find_by_ids(self.user_id, self.module_id, point_id)

    def collect_all(self) -> list[TestPointSession]:
        db.session.delete(self)
        return self.points


class TestPointSession(Base):
    __tablename__ = "test-point-sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ("module_id", "user_id"),
            ("test_module_sessions.module_id", "test_module_sessions.user_id"),
        ),
    )

    module_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    point_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, nullable=False)
    right_answers = Column(Integer, nullable=True)
    total_answers = Column(Integer, nullable=True)
    answers = Column(JSON, nullable=True)

    IndexModel = PydanticModel.column_model(
        point_id, page_id, right_answers, total_answers, answers
    )

    @classmethod
    def find_by_ids(
        cls,
        user_id: int,
        module_id: int,
        point_id: int,
    ) -> TestModuleSession | None:
        return cls.find_first_by_kwargs(
            user_id=user_id,
            module_id=module_id,
            point_id=point_id,
        )
