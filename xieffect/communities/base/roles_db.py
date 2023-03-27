from __future__ import annotations

from collections.abc import Callable
from typing import Self

from flask_fullstack import Identifiable, PydanticModel, TypeEnum
from sqlalchemy import Column, ForeignKey, select
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import count
from sqlalchemy.sql.sqltypes import Integer, String, Enum

from common import Base, db
from common.abstract import SoftDeletable
from communities.base.meta_db import Community, Participant

LIMITING_QUANTITY_ROLES: int = 50


class PermissionType(TypeEnum):
    MANAGE_INVITATIONS = 0
    MANAGE_ROLES = 1


class Role(SoftDeletable, Identifiable):
    __tablename__ = "cs_roles"
    not_found_text = "Role not found"

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    color = Column(String(6), nullable=True)
    community_id = Column(
        Integer,
        ForeignKey(Community.id, ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    permissions = relationship("RolePermission", passive_deletes=True)

    CreateModel = PydanticModel.column_model(name, color)
    IndexModel = CreateModel.column_model(id)

    class FullModel(IndexModel):
        permissions: list[str]

        @classmethod
        def callback_convert(cls, callback: Callable, orm_object: Role, **_) -> None:
            callback(
                permissions=[
                    permission.permission_type.to_string()
                    for permission in orm_object.permissions
                ]
            )

    @classmethod
    def create(
        cls,
        name: str,
        color: str | None,
        community_id: int,
    ) -> Self:
        return super().create(
            name=name,
            color=color,
            community_id=community_id,
        )

    @classmethod
    def find_by_id(cls, entry_id: int) -> Self | None:
        return cls.find_first_not_deleted(id=entry_id)

    @classmethod
    def find_by_community(cls, community_id: int) -> list[Self]:
        return cls.find_all_not_deleted(community_id=community_id)

    @classmethod
    def get_count_by_community(cls, community_id: int) -> int:
        return db.get_first(
            select(count(cls.id)).filter_by(community_id=community_id, deleted=None)
        )


class RolePermission(Base):
    __tablename__ = "cs_role_permissions"

    role_id = Column(
        Integer,
        ForeignKey(Role.id, ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    permission_type = Column(Enum(PermissionType), primary_key=True)

    @classmethod
    def create(
        cls,
        role_id: int,
        permission_type: PermissionType,
    ) -> Self:
        return super().create(
            role_id=role_id,
            permission_type=permission_type,
        )

    @classmethod
    def delete_by_role(cls, role_id: int, permission_type: str) -> None:
        db.session.execute(
            db.delete(cls).where(
                cls.role_id == role_id, cls.permission_type == permission_type
            )
        )

    @classmethod
    def get_all_by_role(cls, role_id: int) -> list[Self]:
        return db.get_all(select(cls).filter_by(role_id=role_id))


class ParticipantRole(Base):  # TODO pragma: no cover
    __tablename__ = "cs_participant_roles"

    participant_id = Column(
        Integer,
        ForeignKey(Participant.id, ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    role_id = Column(
        Integer,
        ForeignKey(Role.id, ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
