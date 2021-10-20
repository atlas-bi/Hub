# Dockerfile for static testing Atlas Automation Hub
#
# build:
# docker build -f static.dockerfile . -t christopherpickering/extract-management-2-static-test
#
# push:
# docker push christopherpickering/extract-management-2-static-test

FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends apt-utils curl pkg-config git > /dev/null

RUN python -m pip install --disable-pip-version-check --quiet tox \
    && curl -sL https://deb.nodesource.com/setup_14.x | bash - > /dev/null \
    && apt-get install -y -qq nodejs > /dev/null \
    && npm set strict-ssl false
