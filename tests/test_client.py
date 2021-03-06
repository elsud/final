import csv
import time

from model.client import Wall
from model.service import Post


def test_init_wall_for_user():
    wall = Wall(1234)
    assert wall.id == 1234
    assert wall.date is None


def test_init_wall_for_group():
    wall = Wall(1234, "1", True)
    assert wall.id == -1234
    assert wall.date == "1"


def test_posts_for_wall():
    wall = Wall(1)
    wall._posts = [1]
    assert wall.posts == [1]


def test_get_csv(tmp_path):
    path = tmp_path / "text.csv"
    wall = Wall(1)
    wall._posts = [Post("id", "date", "text", 1, ["link"], 2, 3, 4)]
    wall.get_csv("id", "text", path=path)
    with open(path, "r") as fi:
        reader = csv.reader(fi)
        for row in reader:
            expected = row
    assert expected == ["id", "text"]


def test_get_statistic_for_period():
    wall = Wall(1)
    wall._posts = [Post("id", 10, "text", 1, ["link"], 1, 1, 1)]
    stat = wall.get_statistic_for_period(wall._posts, "period", 0)
    assert stat.period == "period"
    assert stat.posts == 1
    assert stat.likes == 1.00
    assert stat.comments == 1.00
    assert stat.reposts == 1.00


def test_get_statistic_for_period_handles_zero_division_error():
    wall = Wall(1)
    stat = wall.get_statistic_for_period(wall._posts, "period", 0)
    assert stat.period == "period"
    assert stat.posts == 0
    assert stat.likes == 0
    assert stat.comments == 0
    assert stat.reposts == 0


def test_change_period_with_year():
    result = Wall.change_period("year", "2021", 122)
    assert result[0] == "2020"


def test_change_period_with_month():
    result = Wall.change_period("month", "12.2021", 122)
    assert result[0] == "11.2021"


def test_change_period_with_month_between_two_years():
    result = Wall.change_period("month", "1.2021", 122)
    assert result[0] == "12.2020"


def test_change_period_with_day():
    arg1 = "11.01.2021"
    arg2 = time.mktime(time.strptime(arg1, "%d.%m.%Y"))
    result = Wall.change_period("day", arg1, arg2)
    assert result[0] == "10.01.2021"


def test_change_period_with_day_between_two_months():
    arg1 = "01.01.2021"
    arg2 = time.mktime(time.strptime(arg1, "%d.%m.%Y"))
    result = Wall.change_period("day", arg1, arg2)
    assert result[0] == "31.12.2020"


def test_change_period_with_hour():
    arg1 = "12.11.01.2021"
    arg2 = time.mktime(time.strptime(arg1, "%H.%d.%m.%Y"))
    result = Wall.change_period("hour", arg1, arg2)
    assert result[0] == "11.11.01.2021"


def test_change_period_with_hour_between_two_days():
    arg1 = "00.01.01.2021"
    arg2 = time.mktime(time.strptime(arg1, "%H.%d.%m.%Y"))
    result = Wall.change_period("hour", arg1, arg2)
    assert result[0] == "23.31.12.2020"
