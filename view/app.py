from datetime import datetime, timedelta
from functools import lru_cache, wraps

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from flask import Flask, redirect, render_template, request, send_file, url_for
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField
from wtforms.validators import DataRequired

from config import SECRET_KEY
from model.client import Wall

app = Flask(__name__)
app.secret_key = SECRET_KEY

matplotlib.use("Agg")


class WallForm(FlaskForm):
    """Form for start.html. It has fields for id and date since which get
    posts from wall of user/group and field is_group to correct id.
    """

    id = StringField("Id of group or person", validators=[DataRequired()])
    date = StringField("Since...")
    is_group = BooleanField("Is it a group id?")
    submit = SubmitField("Show")


class DownloadForm(FlaskForm):
    """Form for statistic.html. It has boolean fields to choose what info
    about posts should be downloaded. It can be id of post, text,
    count of attacments, list with links on attachments, count of likes, of
    comments and of reposts.
    """

    id = BooleanField("Add id?")
    text = BooleanField("Add text?")
    attachments = BooleanField("Add count of attachments?")
    links = BooleanField("Add links on attachments?")
    likes = BooleanField("Add count of likes?")
    comments = BooleanField("Add count of comments?")
    reposts = BooleanField("Add count of reposts?")
    submit = SubmitField("Download")


@app.route("/", methods=["GET", "POST"])
def start():
    """Renders start template with form to enter id and date to get posts
    or renders template with information from given wall. If date wasn't
    given it will be set to 0 and rebders template with info about
    all posts on the wall.
    """
    form = WallForm()

    if form.validate_on_submit():
        if not form.date.data:
            form.date.data = 0

        if form.is_group.data:
            return redirect(
                url_for("posts", id=f"-{form.id.data}", date=form.date.data)
            )

        return redirect(url_for("posts", id=form.id.data, date=form.date.data))

    return render_template("start.html", title="Choose id", form=form)


@app.route("/posts/<id>/<date>", methods=["GET", "POST"])
def posts(id: int, date: str):
    """Render template to show info from wall in monthes.
    With choosing another interval or look template will be rerendered.
    Also there's form to choose parameters to download in csv file.
    :param id: id of user or group
    :type id: str
    :param date: date since which search posts
    :type date: str
    :return: redirect or render_template
    """
    form = DownloadForm()
    wall = get_wall(id, date)

    if form.validate_on_submit():
        params = ("id", "text", "attachments", "links", "likes", "comments", "reposts")
        mask = (
            form.id.data,
            form.text.data,
            form.attachments.data,
            form.links.data,
            form.likes.data,
            form.comments.data,
            form.reposts.data,
        )
        args = (item for index, item in enumerate(params) if mask[index])
        wall.get_csv(*args)
        return redirect(url_for("download_file"))

    if request.method == "POST":
        select = request.form.get("interval")
        look = request.form.get("look")
        statistic = wall.get_statistic(select)
        title = f"Statistic in {select}"
        data = (
            (k, v["posts"], v["likes"], v["comments"], v["reposts"])
            for k, v in statistic.items()
        )
        if look == "plot":
            create_plot(data)
            return render_template(
                "plot.html", title=title, form=form, url="/static/images/plot.png"
            )
        return render_template("statistic.html", title=title, data=data, form=form)

    statistic = wall.get_statistic()
    data = (
        (k, v["posts"], v["likes"], v["comments"], v["reposts"])
        for k, v in statistic.items()
    )
    return render_template(
        "statistic.html", title="Statistic in month", data=data, form=form
    )


def timed_lru_cache(seconds: int, maxsize: int = 128):
    """Decorator that changes lru_cache so it keeps information
    during given count of seconds and clears itself afterthat.
    :param seconds: count of seconds to keep data in cache
    :type seconds: int
    :param maxsize: maxsize of cache
    :type maxsize: int
    """

    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.utcnow() + func.lifetime
            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


@timed_lru_cache(300)
def get_wall(id: int, date: str) -> "Wall":
    """Gets Wall instance with given id and date from cache
    or creates it and puts it in cache.
    :param id: id of user or group
    :type id: str
    :param date: date since which search posts
    :type date: str
    :return: Wall instance
    :rtype: Wall
    """
    return Wall(id, date)


def create_plot(data):
    periods, posts, likes, comments, reposts = zip(*data)

    plt.bar(periods, posts, width=0.8, color=["grey"])
    plt.bar(periods, likes, width=0.8, color=["red"])
    plt.bar(periods, comments, width=0.8, color=["green"])
    plt.bar(periods, reposts, width=0.8, color=["blue"])
    plt.xlabel("period", fontsize=11, color="black")
    plt.ylabel("count", fontsize=11, color="black")
    plt.title("statistic of posts' count", fontsize=13, loc="center")
    grey_patch = mpatches.Patch(color="grey", label="Posts")
    red_patch = mpatches.Patch(color="red", label="Likes")
    green_patch = mpatches.Patch(color="green", label="Comments")
    blue_patch = mpatches.Patch(color="blue", label="Reposts")
    plt.legend(handles=[grey_patch, red_patch, green_patch, blue_patch])
    plt.savefig("view/static/images/plot.png")
    plt.close()


@app.route("/download_file")
def download_file():
    """Downloads csv file with statistic."""
    return send_file("../model/files/to_download.csv")


@app.errorhandler(404)
def page_not_found(e):
    """Handler for 404 error."""
    return "Resourse not found. Check given information."


app.register_error_handler(404, page_not_found)

if __name__ == "__main__":
    app.run()
