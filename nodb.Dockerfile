FROM python:3.9

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REMOTE=https://github.com/Riverside-Healthcare/extract_management.git

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
    libxmlsec1-dev \
    libxmlsec1-dev

WORKDIR /app

RUN git -c http.sslVerify=false clone --depth 1 "$REMOTE" . \
    && python -m pip install --disable-pip-version-check poetry \
    && poetry config virtualenvs.create false \
    && poetry install \
    && poetry env info

RUN cp em_web/model.py em_scheduler/ && cp em_web/model.py em_runner/

ENV FLASK_DEBUG=True \
    FLASK_APP=em_web

CMD (FLASK_APP=em_scheduler && flask run --port=5001 &) && (FLASK_APP=em_runner && flask run --port=5002 &) && flask run --host=0.0.0.0 --port=$PORT
