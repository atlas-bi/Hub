FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive \
	FLASK_ENV=test \
    FLASK_DEBUG=1 \
	FLASK_APP=em_web \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends apt-utils curl pkg-config > /dev/null \
	&& apt-get install -y -qq \
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
		postgresql-contrib \
		> /dev/null \
  	&& redis-server --daemonize yes \
  	&& python -m pip install --disable-pip-version-check --quiet poetry \
  	&& su - postgres -c "/etc/init.d/postgresql start && psql --command \"CREATE USER webapp WITH SUPERUSER PASSWORD 'nothing';\"  && createdb -O webapp em_web_test"

WORKDIR /app

RUN git clone --depth 1 https://github.com/Riverside-Healthcare/extract_management . -q \
	&& $(which poetry) install

RUN cp em_web/model.py em_runner/model.py && cp em_web/model.py em_scheduler/model.py

RUN flask db init && flask db migrate && flask db upgrade && flask seed && flask seed demo

CMD (FLASK_APP=em_scheduler && flask run --port=5001 &) && (FLASK_APP=em_runner && flask run --port=5002 &) && flask run --host=0.0.0.0 --port=$PORT
