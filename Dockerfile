FROM ubuntu:14.04
MAINTAINER marcus@abstractfactory.io

# Get system ready
RUN apt-get update
RUN apt-get install -y node python-pygments
RUN apt-get install -y git curl nano 
RUN apt-get install -y python python-dev python-distribute python-pip
RUN apt-get clean
RUN pip install flask gunicorn

EXPOSE 80

VOLUME /app
WORKDIR /app


CMD echo Starting from $(pwd); gunicorn app.app:app --log-file - --bind 0.0.0.0:80
