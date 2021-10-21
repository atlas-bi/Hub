#!/bin/bash
export FLASK_ENV=development
export FLASK_DEBUG=True
export FLASK_APP=web

flask db init
flask db migrate
flask db upgrade
flask cli seed
flask cli seed_demo