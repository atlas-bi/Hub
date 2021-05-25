#!/bin/bash
export FLASK_ENV=development
export FLASK_DEBUG=True
export FLASK_APP=em_web

psql --command "CREATE USER webapp WITH SUPERUSER PASSWORD 'nothing';"
dropdb em_web_dev
createdb -O webapp em_web_dev

flask db init
flask db migrate
flask db upgrade
flask cli seed
flask cli seed_demo
