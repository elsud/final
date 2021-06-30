from unittest.mock import Mock

from model.service import Post, ServiceWall


def test_init_post():
    obj = Post("id", "date", "text", 1, ["link"], 2, 3, 4)
    assert obj.id == "id"
    assert obj.date == "date"
    assert obj.text == "text"
    assert obj.attachments == 1
    assert obj.links == ["link"]
    assert obj.likes == 2
    assert obj.comments == 3
    assert obj.reposts == 4


def test_post_lt_compares_date():
    obj1 = Post("id", 1, "text", 0, ["link"], 0, 0, 0)
    obj2 = Post("id", 5, "text", 0, ["link"], 0, 0, 0)
    assert obj1 < obj2


def test_init_service_wall_with_correct_args():
    wall = ServiceWall(1111, "12.12.2012")
    assert wall.id == 1111
    assert isinstance(wall.date, int)


def test_init_service_wall_with_wrong_date_sets_it_to_zero():
    wall1 = ServiceWall(1111, "abc")
    wall2 = ServiceWall(1111, "12.1")
    wall3 = ServiceWall(1111)
    assert wall1.date == wall2.date == wall3.date == 0


def test_get_links_when_url_in_keys():
    link = ServiceWall.get_links({"url": "link"})
    assert link == "link"


def test_get_links_when_url_in_values():
    link = ServiceWall.get_links({"key": {"url": "link"}})
    assert link == "link"


def test_get_links_when_url_in_list_inside_values():
    link = ServiceWall.get_links({"key": ["value", {"url": "link"}]})
    assert link == "link"
