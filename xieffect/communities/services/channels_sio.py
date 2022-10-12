from __future__ import annotations

from flask_socketio import join_room, leave_room
from pydantic import BaseModel

from common import DuplexEvent, EventController, EventSpace, db
from .channels_db import Category, Channel, ChannelType, MAX_CHANNELS
from ..base.meta_db import ParticipantRole, Community
from ..base.meta_utl import check_participant_role

controller = EventController()


@controller.route()
class ChannelEventSpace(EventSpace):
    @classmethod
    def room_name(cls, community_id: int):
        return f"community-{community_id}"

    class CommunityIdModel(BaseModel):
        community_id: int

    @controller.argument_parser(CommunityIdModel)
    @check_participant_role(controller, ParticipantRole.BASE)
    @controller.force_ack()
    def open_channel(self, community: Community):
        join_room(self.room_name(community.id))

    @controller.argument_parser(CommunityIdModel)
    @check_participant_role(controller, ParticipantRole.BASE)
    @controller.force_ack()
    def close_channel(self, community: Community):
        leave_room(self.room_name(community.id))

    class CreateModel(Channel.CreateModel, CommunityIdModel):
        category_id: int = None
        next_id: int = None

    @controller.doc_abort(400, "Invalid type")
    @controller.doc_abort(409, "Over limit")
    @controller.argument_parser(CreateModel)
    @controller.mark_duplex(Channel.IndexModel, use_event=True)
    @check_participant_role(controller, ParticipantRole.OWNER)
    @controller.marshal_ack(Channel.IndexModel)
    def new_channel(
        self,
        event: DuplexEvent,
        name: str,
        type: str,
        community: Community,
        category_id: int | None,
        next_id: int | None,
    ):
        enum_type: ChannelType = ChannelType.from_string(type)
        if enum_type is None:
            controller.abort(400, f"Invalid type {type}")

        channels_count = len(community.channels)
        if category_id is not None:
            category = Category.find_by_id(category_id)
            channels_count += len(category.channels)

        # Check category limit
        if channels_count == MAX_CHANNELS:
            controller.abort(409, "Over limit: Too many channels")

        channel = Channel.add(
            next_id,
            name=name,
            type=type,
            community_id=community.id,
            category_id=category_id,
        )

        db.session.commit()
        event.emit_convert(channel, self.room_name(community.id))
        return channel
