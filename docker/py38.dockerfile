# Dockerfile for testing Extract Management 2.0 with Python 3.8
#
# build:
# docker build -f py38.dockerfile . -t christopherpickering/extract-management-2-python38-test
#
# push:
# docker push christopherpickering/extract-management-2-python38-test

FROM python:3.8-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends apt-utils curl pkg-config

RUN apt-get install -y \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python-dev \
    python3-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    unixodbc \
    unixodbc-dev \
    redis-server \
    postgresql \
    postgresql-contrib

RUN python -m pip install --disable-pip-version-check --quiet poetry tox
