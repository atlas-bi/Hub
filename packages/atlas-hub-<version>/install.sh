#!/bin/sh

# recommeneded to have ufw installed
#
# ufw default deny > /dev/null
# ufw allow ssh > /dev/null
# ufw allow "Nginx Full" > /dev/null
# ufw --force enable > /dev/null


# Ideally there will be a user config file "/etc/atlas-bi/config". This file will hold
# the database connection, colors and any other user settings.

# If a db has not been added to the file, atlas will show a configuration screen.

# configuration screen is available if there is no db, or a user is superuser.

# After changing the configuration, the app will "reconfigure" - run npm install, db migrate etc.


VERSION=<version>

color() {
  RED=$(printf '\033[31m')
  GREEN=$(printf '\033[32m')
  YELLOW=$(printf '\033[33m')
  BLUE=$(printf '\033[34m')
  UL=$(printf '\033[4m')
  BOLD=$(printf '\033[1m')
  RESET=$(printf '\033[0m') # No Color
}

fmt_error() {
  echo "${RED}Error: $1${RESET}" >&2
}

fmt_install() {
  echo "${YELLOW}Installing: $1${RESET}"
}

fmt_blue() {
  echo "${BLUE}$1${RESET}"
}

fmt_green() {
  echo "${GREEN}$1${RESET}"
}

fmt_yellow() {
  echo "${YELLOW}$1${RESET}"
}

command_install() {
  dpkg -s "$@" 2>&1 |  grep -q 'is not installed' && fmt_install "$@" && apt-get install -q -qq "$@" > /dev/null
}

color

cd /usr/bin/atlas-hub/

echo "${YELLOW}"
echo "

   ###    ######## ##          ###     ######     ##     ## ##     ## ########
  ## ##      ##    ##         ## ##   ##    ##    ##     ## ##     ## ##     ##
 ##   ##     ##    ##        ##   ##  ##          ##     ## ##     ## ##     ##
##     ##    ##    ##       ##     ##  ######     ######### ##     ## ########
#########    ##    ##       #########       ##    ##     ## ##     ## ##     ##
##     ##    ##    ##       ##     ## ##    ##    ##     ## ##     ## ##     ##
##     ##    ##    ######## ##     ##  ######     ##     ##  #######  ########

"

fmt_green "Thanks for installing Atlas Automation Hub!"

# wget -q --show-progress -O- "https://github.com/atlas-bi/atlas-automation-hub/archive/refs/tags/$VERSION.tar.gz" | tar -xz -C .
wget -q --show-progress -O- "https://github.com/atlas-bi/atlas-automation-hub/archive/refs/tags/2021.04.1.tar.gz" | tar -xz -C .

#cd "atlas-automation-hub-$VERSION"
cd "atlas-automation-hub-2021.04.1"

# static should be pre-built in release and not need this command.
# fmt_blue "Building static"
# npm install
# npm run build


# fmt_blue "Updating python settings"
# virtualenv required by Poetry
# $(which python3) -m pip install --disable-pip-version-check --quiet virtualenv > /dev/null

fmt_blue "Installing Poetry"
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(which python3) -

# remove poetry config > it conflicts with install config.
"$HOME/.local/bin/poetry" config --local virtualenvs.in-project true
"$HOME/.local/bin/poetry" config --local virtualenvs.create true
"$HOME/.local/bin/poetry" install --no-dev

fmt_blue "Updating nginx"

touch nginx.log
touch nginx_error.log

rm /etc/nginx/sites-enabled/atlas_bi 2> /dev/null
ln -s publish/nginx /etc/nginx/sites-enabled/atlas_bi


# should only do this if not existing.
# fmt_blue "Setting Up Database"
# su - postgres -c "/etc/init.d/postgresql start && psql --command \"CREATE USER atlas_me WITH SUPERUSER PASSWORD 'nothing';\"  && createdb -O atlas_me atlas_db"

# run database migrations

fmt_blue "Installing SQL Server ODBC"
dpkg -s msodbcsql17 2>&1 |  grep -q 'is not installed' && fmt_install msodbcsql17 \
&& curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
&& curl -fsSL https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
&& apt-get update --q \
&& ACCEPT_EULA=Y apt-get install msodbcsql17 \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.bash_profile \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.bashrc \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.zshrc


# not a docker image.. has systemd installed and running
if [ "$(pidof systemd)" != "" ]; then
    fmt_green "Using systemd as service runner."

    fmt_green "Reloading Nginx!"

    systemctl reload nginx
    systemctl is-active nginx | grep "inactive" && echo "${RED}!!!Failed to reload Nginx!!!${RESET}" && (exit 1)

    fmt_green "Starting Atlas!"
    systemctl enable atlas_bi_celery.service
    systemctl enable atlas_bi_celery_beat.service
    systemctl enable atlas_bi_gunicorn.service

    fmt_green "Starting Redis!"
    fmt_blue "Starting redis server"

    sudo sed -i -e "s/supervised no/supervised systemd/g" /etc/redis/redis.conf > /dev/null
    sudo systemctl enable redis-server > /dev/null
    sudo systemctl start redis-server > /dev/null

else
    # use supervisord
    # supervisord should have
    # - nginx
    # - gunicorn
    # - celery
    # - celerybeat
    # - redis
    fmt_blue "Using supervisor as service runner"
    pkill -f supervisord
    "$HOME/.local/bin/poetry" run supervisord -c ../atlas_bi_supervisord.conf -d "/usr/bin/atlas-bi/atlas-bi-library-py-$VERSION"
fi

# copy model between apps
fmt_blue "Creating API db model"
cp web/model.py runner/model.py
cp web/model.py scheduler/model.py

# install database migrations
fmt_blue "Running database migrations"
export FLASK_ENV=producion && export FLASK_DEBUG=0 && export FLASK_APP=web && .venv/bin/flask db migrate
