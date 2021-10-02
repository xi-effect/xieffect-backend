from json import load
from typing import Callable, Iterator, Optional

from flask.testing import FlaskClient
from pytest import mark

from xieffect.test.components import check_status_code


PAGES_PER_REQUEST: int = 50
MODULES_PER_REQUEST: int = 12


@mark.order(400)
def test_page_list(list_tester: Callable[[str, dict, int], Iterator[dict]]):
    assert len(list(list_tester("/pages", {}, PAGES_PER_REQUEST))) > 0


@mark.order(401)
def test_searching_pages(list_tester: Callable[[str, dict, int], Iterator[dict]]):
    assert len(list(list_tester("/pages", {"search": "Описание test"}, PAGES_PER_REQUEST))) > 0


@mark.order(406)
def test_getting_pages(client: FlaskClient):
    page_json: dict = check_status_code(client.get("/pages/1"))
    for key in ("author_id", "author_name", "views", "updated"):
        page_json.pop(key)

    with open("../files/tfs/test/1.json", "rb") as f:
        assert page_json == load(f)


@mark.order(407)
def test_page_view_counter(client: FlaskClient, list_tester: Callable[[str, dict, int], Iterator[dict]]):
    page_json: dict = check_status_code(client.post("/pages", json={"counter": 0}))[0]
    page_id, views_before = [page_json[key] for key in ["id", "views"]]
    check_status_code(client.get(f"/pages/{page_id}"), get_json=False)

    for page_json in list_tester("/pages", {}, PAGES_PER_REQUEST):
        if page_json["id"] == page_id:
            assert page_json["views"] == views_before + 1
            break
    else:
        raise AssertionError(f"Page with id={page_id} wasn't found")


@mark.order(420)
def test_module_list(list_tester: Callable[[str, dict, int], Iterator[dict]]):
    assert len(list(list_tester("/modules", {}, MODULES_PER_REQUEST))) > 0


def lister_with_filters(list_tester: Callable[[str, dict, int], Iterator[dict]], filters: dict):
    return list_tester("/modules", {"filters": filters}, MODULES_PER_REQUEST)


@mark.order(421)
def test_global_module_filtering(client: FlaskClient, list_tester: Callable[[str, dict, int], Iterator[dict]]):
    filter_to_operation = {
        "pinned": "pin",
        "starred": "star",
    }

    module_id: Optional[int] = None
    for module in list_tester("/modules", {}, MODULES_PER_REQUEST):
        assert "id" in module.keys()
        if not (module["pinned"] or module["starred"]):
            module_id = module["id"]
    assert module_id is not None, "No not-pinned and not-starred modules found"

    url: str = f"/modules/{module_id}/"
    for filter_name, operation_name in filter_to_operation.items():
        assert check_status_code(client.post(url + "preference/", json={"a": operation_name})) == {"a": True}

        result: dict = check_status_code(client.get(url))
        assert result[filter_name] == True

        success: bool = False
        for module in lister_with_filters(list_tester, {"global": filter_name}):
            assert filter_name in module.keys()
            assert module[filter_name]
            if module["id"] == module_id:
                success = True
        assert success, f"Module #{module_id}, marked as {filter_name}, is not found in the list of such modules"


@mark.order(422)
def test_simple_module_filtering(list_tester: Callable[[str, dict, int], Iterator[dict]]):
    filter_map = {
        "theme": ["math", "languages", "geography"],
        "category": ["university", "prof-skills", "bne"],
        "difficulty": ["review", "amateur", "expert"]
    }

    for filter_name, values in filter_map.items():
        for filter_value in values:
            success: bool = False
            for module in lister_with_filters(list_tester, {filter_name: filter_value}):
                assert filter_name in module.keys(), module
                assert module[filter_name] == filter_value, module
                success = True
            assert success, f"No modules found for filter: {filter_name} == {filter_value}"


# @mark.order(423)
# def test_complex_module_filtering(list_tester: Callable[[str, dict, int], Iterator[dict]]):
#     pass


@mark.order(430)
def test_module_search(list_tester: Callable[[str, dict, int], Iterator[dict]]):
    assert len(list(list_tester("/modules", {"search": "ЕГЭ"}, MODULES_PER_REQUEST))) > 0


# @mark.order(435)
# def test_module_sorting(list_tester: Callable[[str, dict, int], Iterator[dict]]):
#     pass