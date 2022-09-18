from __future__ import annotations

from datetime import datetime

from flask_socketio import join_room, leave_room
from pydantic import BaseModel

from common import DuplexEvent, EventController, EventSpace, User, db
from .news_db import Post
from ..base.meta_utl import check_participant_role
from ..base.meta_db import ParticipantRole, Community

controller = EventController()


@controller.route()
class PostEventSpace(EventSpace):
    @classmethod
    def room_name(cls, community_id: int):
        return f"cs-news-{community_id}"

    class CommunityIdModel(BaseModel):
        community_id: int

    @controller.argument_parser(CommunityIdModel)
    @check_participant_role(controller, ParticipantRole.BASE)
    @controller.force_ack()
    def open_news(self, community: Community):
        join_room(self.room_name(community.id))

    @controller.argument_parser(CommunityIdModel)
    @check_participant_role(controller, ParticipantRole.BASE)
    @controller.force_ack()
    def close_news(self, community: Community):
        leave_room(self.room_name(community.id))

    class CreateModel(Post.CreationBaseModel, CommunityIdModel):
        pass

    @controller.argument_parser(CreateModel)
    @controller.mark_duplex(Post.IndexModel, use_event=True)
    @check_participant_role(controller, ParticipantRole.OWNER, use_user=True)
    @controller.marshal_ack(Post.IndexModel)
    def new_post(
        self,
        event: DuplexEvent,
        title: str,
        description: str | None,
        user: User,
        community: Community,
    ):
        post = Post.create(title, description, user.id, community.id)
        db.session.commit()
        event.emit_convert(post, self.room_name(community.id))
        return post

    class UpdateModel(Post.CreationBaseModel, CommunityIdModel):
        post_id: int

    @controller.argument_parser(UpdateModel)
    @controller.mark_duplex(Post.IndexModel, use_event=True)
    @check_participant_role(controller, ParticipantRole.OWNER)
    @controller.database_searcher(Post)
    @controller.marshal_ack(Post.IndexModel)
    def update_post(
        self,
        event: DuplexEvent,
        title: str | None,
        description: str | None,
        community: Community,
        post: Post,
    ):
        if title is not None:
            post.title = title
        if description is not None:
            post.description = description
        if title is not None or description is not None:
            post.changed = datetime.utcnow()
        db.session.commit()

        event.emit_convert(post, self.room_name(community.id))
        return post

    class DeleteModel(CommunityIdModel):
        post_id: int

    @controller.argument_parser(DeleteModel)
    @controller.mark_duplex(DeleteModel, use_event=True)
    @check_participant_role(controller, ParticipantRole.OWNER)
    @controller.database_searcher(Post)
    @controller.force_ack()
    def delete_post(
        self,
        event: DuplexEvent,
        community: Community,
        post: Post,
    ):
        post.deleted = True
        db.session.commit()
        event.emit_convert(
            room=self.room_name(community_id=community.id),
            community_id=community.id,
            post_id=post.id,
        )
