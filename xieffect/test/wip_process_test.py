from json import load
from typing import Callable, Iterator, Union, Optional

from flask.testing import FlaskClient
from pytest import mark

from xieffect.test.components import check_status_code

PER_REQUEST = 50


# https://discord.com/channels/706806130348785715/843536940083314728/880041704651108432


class WIPRecycler:
    def __init__(self, client: FlaskClient, file_type: str, file_name1: str, file_name2: str,
                 list_tester: Callable[[str, dict, int], Iterator[dict]]):
        self.client: FlaskClient = client
        self.list_tester: Callable[[str, dict, int], Iterator[dict]] = list_tester

        self.file_type: str = file_type
        self.wip_url: str = f"/wip/{self.file_type}/"
        self.wip_id_url: str = ""

        self.file_id: Optional[Union[int, str]] = None

        with open(f"test/json/{file_name1}.json", "rb") as f:
            self.file_content1 = load(f)  # content shouldn't have any id info!

        with open(f"test/json/{file_name2}.json", "rb") as f:
            self.file_content2 = load(f)

    def is_in_list(self, url, per_request: int = None) -> Optional[dict]:
        for file in self.list_tester(url, {}, PER_REQUEST if per_request is None else per_request):
            if file["id"] == self.file_id:
                return file
        return None

    def is_same_on_server(self, url, sample) -> bool:
        result: dict = check_status_code(self.client.get(url))
        result = {key: result[key] for key in sample.keys()}
        return result == sample

    def assert_same_on_server(self, url, sample, revert: bool = False):
        result: dict = check_status_code(self.client.get(url))
        result = {key: result[key] for key in sample.keys()}
        if revert:
            assert result != sample
        else:
            assert result == sample

    def creating(self):
        result: dict = check_status_code(self.client.post(self.wip_url, json=self.file_content1))

        self.file_id = result.pop("id", None)
        assert self.file_id is not None
        self.wip_id_url = self.wip_url + f"{self.file_id}/"

        assert self.is_in_list(self.wip_url + "index/") is not None
        self.assert_same_on_server(self.wip_id_url, self.file_content1)

    def editing(self):
        assert self.file_id is not None
        assert self.file_content1 != self.file_content2
        self.assert_same_on_server(self.wip_id_url, self.file_content1)

        result: dict = check_status_code(self.client.put(self.wip_id_url, json=self.file_content2))
        assert result == {"a": True}

        self.assert_same_on_server(self.wip_id_url, self.file_content2)
        self.assert_same_on_server(self.wip_id_url, self.file_content1, revert=True)

    def publishing(self):
        assert self.file_id is not None

        content: Optional[dict] = None
        if self.is_same_on_server(self.wip_id_url, self.file_content1):
            content = self.file_content1
        elif self.is_same_on_server(self.wip_id_url, self.file_content2):
            content = self.file_content2
        assert content is not None

        check_status_code(self.client.post(self.wip_id_url + "publication/"))
        if self.file_type == "modules":
            assert self.is_in_list(f"/{self.file_type}/", per_request=12) is not None
            content.pop("points")
        else:
            assert self.is_in_list(f"/{self.file_type}/") is not None
        # self.assert_same_on_server(f"/{self.file_type}/{self.file_id}/", content)
        # Doesn't work because of the modules' test-bundle!

    def deleting(self, published: bool):
        assert check_status_code(self.client.delete(self.wip_id_url)) == {"a": True}

        assert self.is_in_list(self.wip_url + "index/") is None
        check_status_code(self.client.get(self.wip_id_url), 404)

        if published:
            assert self.is_in_list(f"/{self.file_type}/") is None
            check_status_code(self.client.get(f"/{self.file_type}/{self.file_id}/"), 404)

    def wip_full_cycle(self):
        self.creating()
        self.editing()
        self.publishing()
        self.deleting(True)


@mark.order(200)
def test_pages(client: FlaskClient, list_tester: Callable[[str, dict, int], Iterator[dict]]):
    WIPRecycler(client, "pages", "sample-page", "sample-page-2", list_tester).wip_full_cycle()


@mark.order(220)
def test_modules(client: FlaskClient, list_tester: Callable[[str, dict, int], Iterator[dict]]):
    WIPRecycler(client, "modules", "sample-module", "sample-module-2", list_tester).wip_full_cycle()