FROM python:3.10

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REMOTE=https://github.com/atlas-bi/atlas-automation-hub.git

RUN apt-get update -qq \
     && apt-get install -y -qq --no-install-recommends apt-utils curl pkg-config postgresql-contrib > /dev/null

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

RUN git -c http.sslVerify=false clone --depth 1 "$REMOTE" . \
    && python -m pip install --disable-pip-version-check poetry \
    && poetry config virtualenvs.create false \
    && poetry install \
    && poetry env info

RUN cp web/model.py scheduler/ && cp web/model.py runner/

ENV FLASK_ENV=development \
    FLASK_DEBUG=False \
    FLASK_APP=web

CMD (FLASK_APP=scheduler && flask run --port=5001 &) && (FLASK_APP=runner && flask run --port=5002 &) && flask run --host=0.0.0.0 --port=$PORT
