# needs a DATABASE_URL and REDIS_URL to be set

# setup python
FROM python:3.10-alpine as python_install

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apk update \
    && apk add --no-cache build-base gcc libxml2-dev libxslt-dev musl-dev libressl libffi-dev libressl-dev xmlsec-dev xmlsec unixodbc-dev openldap-dev

WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN wget -O - https://install.python-poetry.org | python3 - \
 && chmod 755 ${POETRY_HOME}/bin/poetry \
 && poetry install --no-root --no-dev

# build assets
FROM python:3.10-alpine as assets

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    FLASK_ENV=demo \
    FLASK_DEBUG=False \
    FLASK_APP=web

ARG DATABASE_URL \
    REDIS_URL

WORKDIR /app

COPY --from=python_install /app/.venv ./.venv
COPY migrations ./migrations
COPY web ./web
COPY runner ./runner
COPY scheduler ./scheduler
COPY scripts ./scripts
COPY config.py pyproject.toml ./

RUN cp web/model.py scheduler/ && cp web/model.py runner/ \
 && apk update && apk add --no-cache openldap-dev unixodbc-dev \
 && flask assets build \
 && flask cli reset_db && flask db upgrade && flask cli seed && flask cli seed_demo

# final app
FROM python:3.10-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    FLASK_ENV=demo \
    FLASK_DEBUG=False \
    FLASK_APP=web

ARG DATABASE_URL \
    REDIS_URL

RUN apk update && apk add --no-cache openldap-dev unixodbc-dev

WORKDIR /app

COPY --from=assets app ./

EXPOSE $PORT
CMD (FLASK_APP=scheduler && flask run --port=5001 &) && (FLASK_APP=runner && flask run --port=5002 &) && flask run --host=0.0.0.0 --port=$PORT
