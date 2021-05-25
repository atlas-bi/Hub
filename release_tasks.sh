#!/bin/bash
export FLASK_ENV=development
export FLASK_DEBUG=True
export FLASK_APP=em_web

psql --command "CREATE USER webapp WITH SUPERUSER PASSWORD 'nothing';"
createdb -O webapp em_web_test

flask db init
flask db migrate
flask db upgrade
flask cli seed
flask cli seed_demo
