"""Module with class 'Wall' which uses 'ServiceWall' to get info about posts
on the interesting wall since interesting date. Afterthat 'Wall' can get
ststistic on count of posts and average counts of likes, comments and reposts
in some period (year, month, day or hour). Also it can write choosen
info about posts in csv file.
"""

import csv
import datetime
import time
from typing import Tuple, Union

from model.service import ServiceWall


class Statistic:
    """Keeps statistic information about count of posts and
    average counts of likes, comments, reposts for one period.
    :param period: period, for example '23.12.2020'
    :type period: str
    :param posts: count of posts
    :type posts: int
    :param likes: count of likes
    :type likes: float
    :param comments: count of comments
    :type comments: float
    :param reposts: count of reposts
    :type reposts: float
    """

    __slots__ = ("period", "posts", "likes", "comments", "reposts")

    def __init__(self, period, posts, likes, comments, reposts):

        self.period = period
        self.posts = posts
        self.likes = likes
        self.comments = comments
        self.reposts = reposts


class Wall:
    """Class for user's or group's wall representation.
    Implements ability to get information about posts in statistics or
    to download it in csv.
    :param id: id of group or user
    :type id: int
    :param date: date to get posts since
    :type date: str or None
    :param group: is it a group id
    :type group: bool
    """

    def __init__(
        self, id: int, date: Union[str, None] = None, group: bool = False
    ) -> None:
        self.id = -id if group else id
        self.date = date
        self._posts = []

    @property
    def posts(self) -> list:
        """Top up '_posts' using ServiceWall.
        :return: list with Post objects
        :rtype: list"""
        if not self._posts:
            wall = ServiceWall(self.id, self.date)
            wall.get_all_posts()
            self._posts = wall._posts
        return self._posts

    def get_csv(
        self, *args: Tuple[str], path: str = "model/files/to_download.csv"
    ) -> None:
        """Writes chosen info about posts on the wall in csv file.
        :param args: what info should be written (id, text, attachments, links,
        likes, comments, reposts)
        :type args: tuple with str
        :param path: path to csv file to write info in
        :type path: str
        """
        with open(path, "w") as report:
            writer = csv.writer(report)
            writer.writerow(args)
            for post in self.posts:
                writer.writerow((str(post.__getattribute__(arg)) for arg in args))

    @staticmethod
    def get_statistic_for_period(posts: list, period: str, point: int) -> dict:
        """Pick statistic (count of posts, average count of likes, comments,
        reposts) for one period.
        :param posts: list of posts to get statistic info
        :type posts: list
        :param period: period to get posts (for example '3.2021')
        :type period: str
        :param point: timestamp of the beginning of the period
        :type point: int
        :return: dict of statistics with period as key
        :rtype: dict
        """
        posts_count, likes_count, comments_count, reposts_count = 0, 0, 0, 0
        for post in posts:
            if post.date < point:
                break
            posts_count += 1
            likes_count += post.likes
            comments_count += post.comments
            reposts_count += post.reposts
        if posts_count:
            likes_count = round(likes_count / posts_count, 2)
            comments_count = round(comments_count / posts_count, 2)
            reposts_count = round(reposts_count / posts_count, 2)

        return Statistic(
            period, posts_count, likes_count, comments_count, reposts_count
        )

    @staticmethod
    def change_period(duration: str, period: str, point: float) -> Tuple[str, float]:
        """Change period on previous.
        :param duration: duration of period (year, month, day, hour)
        :type duration: str
        :param period: what exactly period (for example '3.2021')
        :type period: str
        :param point: timestamp of the beginning of the period
        :type point: float
        :return: tuple with new period and point of its beginning
        :rtype: tuple
        """
        if duration == "month":
            month, year = tuple(map(int, period.split(".")))
            if month > 1:
                month -= 1
            else:
                year -= 1
                month = 12
            period = f"0{month}.{year}" if month < 10 else f"{month}.{year}"
            point = time.mktime(time.strptime(period, "%m.%Y"))

        if duration == "year":
            period = str(int(period) - 1)
            point = time.mktime(time.strptime(period, "%Y"))

        if duration == "day":
            seconds_in_day = 86400
            point = point - seconds_in_day
            period = datetime.datetime.fromtimestamp(point).strftime("%d.%m.%Y")

        if duration == "hour":
            seconds_in_hour = 3600
            point = point - seconds_in_hour
            period = datetime.datetime.fromtimestamp(point).strftime("%H.%d.%m.%Y")

        return period, point

    @staticmethod
    def get_period(duration: str) -> Tuple[str, int]:
        """Get period and timestamp of its beginning.
        :param duration: duration of period (year, month, day, hour)
        :type duration: str
        :return: tuple with period and timestamp of its beginning
        :rtype: tuple with str and float
        """

        if duration == "month":
            period = datetime.date.today().strftime("%m.%Y")
            point = time.mktime(time.strptime(period, "%m.%Y"))
        if duration == "year":
            period = datetime.date.today().strftime("%Y")
            point = time.mktime(time.strptime(period, "%Y"))
        if duration == "day":
            period = datetime.date.today().strftime("%d.%m.%Y")
            point = time.mktime(time.strptime(period, "%d.%m.%Y"))
        if duration == "hour":
            period = datetime.datetime.now().strftime("%H.%d.%m.%Y")
            point = time.mktime(time.strptime(period, "%H.%d.%m.%Y"))
        return period, point

    def get_statistic(self, duration: str = "month") -> dict:
        """Pick statistic (count of posts, average count of likes, comments,
        reposts) for all periods.
        :param duration: duration of period to get statistics (year, month, day or hour)
        :type point: str
        :return: dict of statistics with periods as keys
        :rtype: dict
        """
        period, point = Wall.get_period(duration)
        posts = self.posts
        length = 0
        while length < len(posts):
            statistic = self.get_statistic_for_period(posts[length:], period, point)
            length += statistic.posts
            period, point = Wall.change_period(duration, period, point)
            yield statistic
