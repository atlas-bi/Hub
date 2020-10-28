FROM alpine:latest
RUN apk update
RUN apk add vim

RUN apk add --no-cache git curl python3 build-base openldap-dev python3-dev tzdata libffi-dev openssl-dev sqlite unixodbc-dev postgresql-dev libxml2 libxslt libxslt-dev libxml2-dev xmlsec xmlsec-dev \
	&& cp /usr/share/zoneinfo/America/Chicago /etc/localtime && echo "America/Chicago" > /etc/timezone \
	&& apk del tzdata \
	&& ln -sf python3 /usr/bin/python

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	FLASK_APP=em

RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools wheel

RUN curl -k -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.6.1.1-1_amd64.apk \
	&& apk add --allow-untrusted msodbcsql17_17.6.1.1-1_amd64.apk

WORKDIR /app

RUN git clone https://github.com/Riverside-Healthcare/extract_management . \
	&& pip3 install -e . 

RUN python manage.py db init \
	&& python manage.py db migrate \
	&& python manage.py db upgrade \
	&& sqlite3 em.sqlite ".read seed.sql"

CMD flask run --host=0.0.0.0 --port=$PORT
