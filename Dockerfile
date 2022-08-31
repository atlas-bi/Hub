# needs a DATABASE_URL and REDIS_URL to be set
FROM nikolaik/python-nodejs:python3.10-nodejs18

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update -qq \
     && apt-get install -y -qq --no-install-recommends apt-utils pkg-config postgresql-contrib > /dev/null

RUN apt-get install -y -qq \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    git \
    wget \
    libldap2-dev \
    python3-dev \
    python3-pip \
    python3-setuptools \
    unixodbc \
    unixodbc-dev \
    libsqlite3-0 \
    libsasl2-dev \
    libxml2-dev \
    libxmlsec1-dev

WORKDIR /app

COPY . .

RUN npm install

ARG DATABASE_URL \
    REDIS_URL

RUN python -m pip install --disable-pip-version-check poetry==1.1.15 \
    && poetry config virtualenvs.create false \
    && poetry install \
    && poetry env info

RUN cp web/model.py scheduler/ && cp web/model.py runner/

ENV FLASK_ENV=demo \
    FLASK_DEBUG=False \
    FLASK_APP=web

RUN flask cli reset_db && flask db upgrade && flask cli seed && flask cli seed_demo

EXPOSE $PORT
CMD (FLASK_APP=scheduler && flask run --port=5001 &) && (FLASK_APP=runner && flask run --port=5002 &) && flask run --host=0.0.0.0 --port=$PORT
