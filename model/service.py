"""Module has service classes of 'Post' and 'ServiceWall'.
'Post' keeps info about one post. 'ServiceWall' takes id of the wall's
owner and date since which posts on the wall are interesting.
It can get all corresponding posts and put it in attribute '.posts'
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Union

import requests

from config import API, TOKEN, V

thread_local = threading.local()


class Post:
    """Class that represent info about wall's posts.
    :param id: id of the post
    :type id: int
    :param date: date of the post's publication
    :type date: int
    :param text: text of the post
    :type text: string
    :param attachments: count of attachments
    :type attachments: int
    :param links: links on attachments
    :type links: list
    :param likes: count of likes
    :type likes: int
    :param comments: count of comments
    :type comments: int
    :param reposts: count of reposts
    :type reposts: int
    """

    def __init__(
        self,
        id: int,
        date: int,
        text: str,
        attachments: int,
        links: List[str],
        likes: int,
        comments: int,
        reposts: int,
    ) -> None:
        self.id = id
        self.date = date
        self.text = text
        self.links = links
        self.attachments = attachments
        self.likes = likes
        self.comments = comments
        self.reposts = reposts

    def __lt__(self, other):
        """Compares instances of Post by their date."""
        return self.date < other.date

    def __repr__(self) -> str:
        """String representation of Post's instances."""
        return str(self.id)


class ServiceWall:
    """Service class to save info about all posts from the wall since
    given date.
    :param id: id of the user or the group, group id should start with '-'
    :type id: int
    :param date: date to get posts since
    :type date: str or None, after init it will be int
    :param _posts: list for saving posts from the wall
    :type _posts: list
    """

    def __init__(self, id: int, date: Union[str, None] = None) -> None:
        self.id = id
        try:
            self.date = int(time.mktime(time.strptime(date, "%d.%m.%Y")))
        except (ValueError, TypeError):
            self.date = 0
        self._posts = []

    @staticmethod
    def get_session():
        """Gets requests.Session for one thread."""
        if not hasattr(thread_local, "session"):
            thread_local.session = requests.Session()
        return thread_local.session

    def get_posts(self, offset: int = 0) -> bool:
        """Get 100 or less posts from the wall and put it in '_posts'.
        If date from which we search posts is reached function stops get posts
        and returns False.
        :param offset: shift in search
        :type offset: int
        :return: if search should be continued
        :rtype: bool
        """
        flag = True
        params = (
            f"owner_id={self.id}&count=100&offset={offset}&access_token={TOKEN}&v={V}"
        )
        url = f"{API}/wall.get?{params}"
        session = self.get_session()
        with session.get(url) as response:
            info = response.json().get("response", {}).get("items", {})
            for item in info:
                if item["date"] < self.date:
                    flag = False
                    break
                id = item["id"]
                date = item["date"]
                text = item["text"]
                links = []
                is_attachments = item.get("attachments", None)
                if is_attachments:
                    for element in item["attachments"]:
                        links.append(ServiceWall.get_links(element))
                attachments = len(item["attachments"]) if is_attachments else 0
                likes = item.get("likes", {}).get("count", 0)
                reposts = item.get("reposts", {}).get("count", 0)
                comments = item["comments"]["count"]
                post = Post(
                    id, date, text, attachments, links, likes, comments, reposts
                )
                self._posts.append(post)
            if len(info) < 100:
                flag = False
        return flag

    @staticmethod
    def get_links(item: dict) -> Union[str, None]:
        """Get links on attachments.
        :param item: json object with info about attachments
        :type item: dict
        :return: link on attachment
        :rtype: str or None
        """
        for key, value in item.items():
            if key == "url":
                return value
            if hasattr(value, "items"):
                return ServiceWall.get_links(value)
            if isinstance(value, list):
                try:
                    return ServiceWall.get_links(value[-1])
                except IndexError:
                    continue
        return None

    def get_all_posts(self) -> None:
        """Get all suitable posts from the wall and put it in '_posts'
        using threads to do it faster. sorts '_posts' by date."""

        def inner(start: int) -> bool:
            """Get posts with 36 threads.
            :param start: shift from which we are searching
            :type start: int
            :return: if get posts should be continued
            :rtype: bool
            """
            with ThreadPoolExecutor(max_workers=36) as pool:
                result = pool.map(self.get_posts, range(start, start + 3501, 100))
                return all(result)

        start = 0
        while inner(start):
            start += 3500
        self._posts.sort(reverse=True)
