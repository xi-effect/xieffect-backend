from __future__ import annotations

from functools import wraps

from flask_fullstack import EventSpace, DuplexEvent
from flask_socketio import leave_room, join_room
from pydantic import BaseModel, Field

from common import EventController, db
from .meta_db import Community, ParticipantRole
from .roles_db import Role, RolePermission, PermissionType, LIMITING_QUANTITY_ROLES
from ..utils import check_participant

controller = EventController()


def check_permissions(function):
    @wraps(function)
    @controller.doc_abort(400, "Incorrect permissions")
    def check_permissions_wrapper(*args, permissions: list[str] | None, **kwargs):
        if permissions is not None:
            permissions = [
                PermissionType.from_string(permission) for permission in permissions
            ]

            if any(permission is None for permission in permissions):
                controller.abort(400, "Incorrect permissions")

        return function(*args, permissions=permissions, **kwargs)

    return check_permissions_wrapper


@controller.route()
class RolesEventSpace(EventSpace):
    @classmethod
    def room_name(cls, community_id: int):
        return f"cs-roles-{community_id}"

    class CommunityIdModel(BaseModel):
        community_id: int

    @controller.argument_parser(CommunityIdModel)
    @check_participant(controller)
    @controller.force_ack()
    def open_roles(self, community: Community):
        join_room(self.room_name(community.id))

    @controller.argument_parser(CommunityIdModel)
    @check_participant(controller)
    @controller.force_ack()
    def close_roles(self, community: Community):
        leave_room(self.room_name(community.id))

    class CreateModel(Role.CreateModel, CommunityIdModel):
        permissions: list[str] = Field(default_factory=list)

    @controller.doc_abort(400, "Quantity exceeded")
    @controller.argument_parser(CreateModel)
    @controller.mark_duplex(Role.FullModel, use_event=True)
    @check_participant(controller, role=ParticipantRole.OWNER)
    @check_permissions
    @controller.marshal_ack(Role.FullModel)
    def new_role(
        self,
        event: DuplexEvent,
        name: str,
        color: str | None,
        permissions: list[str],
        community: Community,
    ):
        if Role.get_count_by_community(community.id) >= LIMITING_QUANTITY_ROLES:
            controller.abort(400, "Quantity exceeded")
        role = Role.create(name=name, color=color, community_id=community.id)

        for permission in permissions:
            RolePermission.create(
                role_id=role.id,
                permission_type=permission,
            )

        db.session.commit()
        event.emit_convert(role, self.room_name(community.id))
        return role

    class UpdateModel(Role.CreateModel, CommunityIdModel):
        permissions: list[str] = None
        role_id: int

    @controller.argument_parser(UpdateModel)
    @controller.mark_duplex(Role.FullModel, use_event=True)
    @check_participant(controller, role=ParticipantRole.OWNER)
    @check_permissions
    @controller.database_searcher(Role)
    @controller.marshal_ack(Role.FullModel)
    def update_role(
        self,
        event: DuplexEvent,
        name: str | None,
        color: str | None,
        permissions: list[str] | None,
        community: Community,
        role: Role,
    ):
        if name is not None:
            role.name = name
        if color is not None:
            role.color = color
        if permissions is not None:
            received_permissions: set[PermissionType] = set(permissions)
            permissions_from_db: set[PermissionType] = {
                permission.permission_type
                for permission in RolePermission.get_all_by_role(role.id)
            }

            for del_permission in permissions_from_db.difference(received_permissions):
                RolePermission.delete_by_role(
                    role_id=role.id, permission_type=del_permission
                )

            for permission in received_permissions.intersection(permissions_from_db):
                received_permissions.remove(permission)

            for permission in received_permissions.difference(permissions_from_db):
                RolePermission.create(
                    role_id=role.id,
                    permission_type=permission,
                )

        db.session.commit()
        event.emit_convert(role, self.room_name(community.id))
        return role

    class DeleteModel(CommunityIdModel):
        role_id: int

    @controller.argument_parser(DeleteModel)
    @controller.mark_duplex(DeleteModel, use_event=True)
    @check_participant(controller, role=ParticipantRole.OWNER)
    @controller.database_searcher(Role)
    @controller.force_ack()
    def delete_role(
        self,
        event: DuplexEvent,
        role: Role,
        community: Community,
    ):
        role.delete()
        db.session.commit()
        event.emit_convert(
            room=self.room_name(community.id),
            community_id=community.id,
            role_id=role.id,
        )