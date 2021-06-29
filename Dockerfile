FROM python:3.9-slim-buster

ENV FLASK_APP=/app/view/app.py

RUN mkdir /app

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt


CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
