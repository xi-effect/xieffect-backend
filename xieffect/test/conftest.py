from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Protocol

from flask.testing import FlaskClient
from flask_fullstack import check_code
from pytest import fixture
from pytest_mock import MockerFixture
from werkzeug.test import TestResponse

from common import User, mail, mail_initialized, Base, db
from common.testing import SocketIOTestClient
from communities.base import CommunitiesUser
from wsgi import application as app, BASIC_PASS, TEST_EMAIL, TEST_MOD_NAME, TEST_PASS


class RedirectedFlaskClient(FlaskClient):
    def open(self, *args, **kwargs):  # noqa: A003
        kwargs["follow_redirects"] = True
        return super().open(*args, **kwargs)


app.test_client_class = RedirectedFlaskClient


@fixture(scope="session", autouse=True)
def application_context() -> None:
    with app.app_context():
        yield


@fixture(scope="session", autouse=True)
def base_client():
    app.debug = True
    with app.test_client() as client:
        yield client


def base_login(client: FlaskClient, account: str, password: str, mub: bool = False) -> None:
    response: TestResponse = client.post(
        "/mub/sign-in/" if mub else "/signin/",
        data={"username" if mub else "email": account, "password": password}
    )
    assert response.status_code == 200
    assert "Set-Cookie" in response.headers
    cookie: tuple[str, str] = response.headers["Set-Cookie"].partition("=")[::2]
    assert cookie[0] == "access_token_cookie"
    client.set_cookie("test", "access_token_cookie", cookie[1])


def login(account: str, password: str, mub: bool = False) -> FlaskClient:
    with app.test_client() as client:
        base_login(client, account, password, mub)
        return client


@fixture
def client() -> FlaskClient:
    return login(TEST_EMAIL, BASIC_PASS)


@fixture
def mod_client() -> FlaskClient:
    return login(TEST_MOD_NAME, TEST_PASS, mub=True)


@fixture
def full_client() -> FlaskClient:
    test_client = login(TEST_EMAIL, BASIC_PASS)
    base_login(test_client, TEST_MOD_NAME, TEST_PASS, mub=True)
    return test_client


@fixture
def multi_client() -> Callable[[str], FlaskClient]:
    def multi_client_inner(user_email: str):
        return login(user_email, BASIC_PASS)

    return multi_client_inner


@fixture
def socketio_client(client: FlaskClient) -> SocketIOTestClient:  # noqa: WPS442
    return SocketIOTestClient(client)


class ListTesterProtocol(Protocol):
    def __call__(
        self,
        link: str,
        request_json: dict,
        page_size: int,
        status_code: int = 200,
        use_post: bool = False,
    ) -> Iterator[dict]:
        pass


@fixture
def list_tester(full_client: FlaskClient) -> ListTesterProtocol:  # noqa: WPS442
    def list_tester_inner(
        link: str,
        request_json: dict,
        page_size: int,
        status_code: int = 200,
        use_post: bool = False,
    ) -> Iterator[dict]:
        counter = 0
        amount = page_size
        while amount == page_size:
            request_json["counter"] = counter
            response_json: dict = check_code(
                full_client.open(
                    link,
                    json=request_json,
                    method="POST" if use_post else "GET",
                ),
                status_code,
            )
            assert "results" in response_json
            assert isinstance(response_json["results"], list)
            yield from response_json["results"]

            amount = len(response_json["results"])
            assert amount <= page_size

            counter += 1

        assert counter > 0

    return list_tester_inner


@fixture
def mock_mail(mocker: MockerFixture):
    with mail.record_messages() as outbox:
        if not mail_initialized:
            mocker.patch("other.emailer.mail_initialized", side_effect=True)
            mocker.patch("common._core.mail.send", lambda params: outbox.append(params))
        yield outbox


@fixture(scope="session")
def test_user_id() -> int:
    return User.find_by_email_address("test@test.test").id


def delete_by_id(entry_id: int, table: type[Base]) -> None:
    orm_object = table.find_first_by_kwargs(id=entry_id)
    if orm_object is not None:
        orm_object.delete()
        db.session.commit()
    assert table.find_first_by_kwargs(id=entry_id) is None


@fixture
def base_user_id() -> int:
    user_id = User.create(
        email="hey@hey.hey",
        password="12345",
        username="hey",
    ).id
    CommunitiesUser.find_or_create(user_id)  # TODO remove after CU removal
    db.session.commit()
    yield user_id
    delete_by_id(user_id, User)
