from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient
from flask_socketio.test_client import SocketIOTestClient as _SocketIOTestClient

from __lib__.flask_fullstack import dict_equal
from common import SocketIO


class SocketIOTestClient(_SocketIOTestClient):
    def __init__(self, flask_client: FlaskClient):
        app: Flask = flask_client.application
        socketio: SocketIO = app.extensions["socketio"]
        super().__init__(app, socketio, flask_test_client=flask_client)

    def count_received(self):
        return len(self.queue[self.eio_sid])

    def assert_nop(self):
        assert self.count_received() == 0

    def assert_emit_ack(
        self,
        event_name: str,
        *args,
        code: int = 200,
        message: str | None = None,
        get_data: bool = True,
        with_nop: bool = True,
        **kwargs,
    ):
        kwargs["callback"] = True
        ack = self.emit(event_name, *args, **kwargs)

        if with_nop:
            self.assert_nop()

        assert isinstance(ack, dict)
        assert ack.get("code", None) == code
        if message is not None:
            assert ack.get("message", None) == message

        if get_data:
            return ack.get("data", None)
        return ack

    def assert_received(self, event_name: str, data: dict, *, pop: bool = True) -> dict:
        result: list[tuple[..., int]] = [
            (pkt, i)
            for i, pkt in enumerate(self.queue[self.eio_sid])
            if pkt["name"] == event_name
        ]

        assert len(result) == 1
        pkt, i = result[0]
        event_data = pkt["args"][0]
        assert dict_equal(event_data, data, *data.keys())

        if pop:
            self.queue[self.eio_sid].pop(i)

        return event_data

    def assert_only_received(self, event_name: str, data: dict) -> dict:
        assert self.count_received() == 1
        return self.assert_received(event_name, data)

    @staticmethod
    def assert_broadcast(
        event_name: str,
        data: dict,
        *clients: SocketIOTestClient,
        pop: bool = True,
    ) -> None:
        for client in clients:
            client.assert_received(event_name, data, pop=pop)

    @staticmethod
    def assert_bulk_nop(*clients: SocketIOTestClient) -> None:
        for client in clients:
            client.assert_nop()
