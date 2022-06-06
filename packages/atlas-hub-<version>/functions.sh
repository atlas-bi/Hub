#!/bin/sh

color() {
  RED=$(printf '\033[31m')
  GREEN=$(printf '\033[32m')
  YELLOW=$(printf '\033[33m')
  BLUE=$(printf '\033[34m')
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


name() {
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
  echo "$RESET"

}

install_configuration(){
  # install default configuration if missing
  if [ ! -e "$USER_DIR/config.ini" ]
  then
    if [ ! -d "$USER_DIR" ]; then
      mkdir -p "$USER_DIR"
    fi
    # apply initial external url
    sed -i -e "s/EXTERNAL_URL='localhost'/EXTERNAL_URL='${EXTERNAL_URL}'/g" "$BASE_DIR/config.ini" > /dev/null
    cp "$BASE_DIR/config.ini" /etc/atlas-hub/config.ini
  fi
}

stop_services(){
  BASE_DIR="/usr/lib/atlas-hub"
  INSTALL_DIR="$BASE_DIR/app"

  if [ "$(pidof systemd)" != "" ]; then
    systemctl stop nginx
    systemctl stop atlas_hub_web.service
    systemctl stop atlas_hub_runner.service
    systemctl stop atlas_hub_scheduler.service
  else


    # try with supervisorctl
    if [ -e "$INSTALL_DIR/.venv/bin/supervisorctl" ]; then
        "$INSTALL_DIR/.venv/bin/supervisorctl" -c "$BASE_DIR/supervisord.conf" stop all && sleep 3
    fi

    # stop any supervisord process
    if [ -e "$BASE_DIR/supervisord.pid" ]; then
      kill -15 "$(cat "$BASE_DIR/supervisord.pid")" && sleep 3s
      if [ -x "$(pgrep supervisord)" ];  then
          pkill supervisord 2>/dev/null
      fi
    fi

    /etc/init.d/nginx stop

  fi
}

start_services(){
  if [ "$(pidof systemd)" != "" ]; then

      systemctl enable nginx
      systemctl start nginx
      systemctl is-active nginx | grep "inactive" && echo "${RED}!!!Failed to reload Nginx!!!${RESET}" && (exit 1)

      systemctl enable atlas_hub_web.service
      systemctl enable atlas_hub_runner.service
      systemctl enable atlas_hub_scheduler.service

      systemctl start atlas_hub_web.service
      systemctl start atlas_hub_runner.service
      systemctl start atlas_hub_scheduler.service

      fmt_green "Starting Redis!"
      fmt_blue "Starting redis server"

      sed -i -e "s/supervised no/supervised systemd/g" /etc/redis/redis.conf > /dev/null
      systemctl enable redis-server > /dev/null
      systemctl start redis-server > /dev/null

  else
      # use supervisord
      # supervisord should have
      # - nginx
      # - gunicorn x3
      # - redis

      # update redis confg
      /etc/init.d/redis-server start
      /etc/init.d/nginx start
      /etc/init.d/postgresql start

      "$INSTALL_DIR/.venv/bin/python" -m pip install supervisor gevent gunicorn -q
      "$INSTALL_DIR/.venv/bin/supervisord" -c "$BASE_DIR/supervisord.conf" -e debug
      "$INSTALL_DIR/.venv/bin/supervisorctl" -c "$BASE_DIR/supervisord.conf" start all


      # cd /usr/lib/atlas-hub/atlas-automation-
      # .venv/bin/supervisord -c ../supervisord.conf -e debug
      # run supervisorctl
      # .venv/bin/supervisorctl -c ../supervisord.conf
      #  tail -F /var/log/nginx/error.log
      #  tail -F /var/log/atlas-hub/error.log
      # tail -F /var/log/atlas-hub/supervisord.log
  fi
}

postgres_init(){

    # ensure pg is running
    /etc/init.d/postgresql start 1>/dev/null

    #  call function by "postgres_init $BASE_DIR"
    PASS=$(jq .PG_PASS < "$1/secrets.json")

    # setup user
    if [ ! "$( su - postgres -c "psql -tAc \"SELECT 1 FROM pg_roles where pg_roles.rolname = 'atlas_me'\"" )" = '1' ]; then
        su - postgres -c "psql --command \"CREATE USER atlas_me WITH PASSWORD '$PASS';\""
    else
        su - postgres -c "psql --command \"ALTER USER atlas_me WITH PASSWORD '$PASS';\"" 1>/dev/null
    fi

    if [ ! "$( su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='atlas_hub'\"" )" = '1' ]; then
        su - postgres -c "createdb -O atlas_me atlas_hub"
    fi
}

postgres_default_user(){

    # ensure pg is running
    /etc/init.d/postgresql start 1>/dev/null

    if [ ! "$( su - postgres -c "psql -d atlas_hub -tAc \"SELECT 1 FROM atlas_hub.public.user WHERE account_name='admin'\" " )" = '1' ]; then
        su - postgres -c "psql -d atlas_hub -c \"INSERT INTO atlas_hub.public.user (account_name, full_name, first_name) VALUES ('admin', 'admin','admin')\""
    fi
}

recommendations(){

  # recommend ufw
  dpkg -s ufw 2>&1 | grep 'is not installed' >/dev/null && cat <<EOF
${YELLOW}
Sercure your server with ufw!

    ${BLUE}apt install ufw${RESET}

Recommended settings:
${BLUE}
    ufw default deny
    ufw allow ssh
    ufw allow \"Nginx Full\"
    ufw --force enable
${RESET}
EOF

  dpkg -s msodbcsql17 2>&1 | grep 'is not installed' >/dev/null && cat <<EOF
${YELLOW}
msodbcsql17 is required to connect to SQL Server databases.
${RESET}

See documentation at https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15
${BLUE}
    sudo curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
    sudo curl -fsSL https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
    sudo apt-get update
    sudo ACCEPT_EULA=Y apt-get install msodbcsql18
${RESET}
EOF

}

gunicorn_services(){
  cat <<EOT > /etc/systemd/system/atlas_hub_web.service
[Unit]
Description=Atlas Automation Hub Web / Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/usr/lib/atlas-hub/app
Environment="PATH=/usr/lib/atlas-hub/app/.venv/bin"
ExecStart=/usr/lib/atlas-hub/app/.venv/bin/gunicorn --worker-class=gevent --workers 1 --threads 30 --timeout 999999999 --access-logfile /var/log/atlas-hub/access.log --error-logfile /var/log/atlas-hub/error.log --capture-output --bind  unix:web.sock --umask 007 web:app

[Install]
WantedBy=multi-user.target
EOT
  cat <<EOT > /etc/systemd/system/atlas_hub_runner.service
[Unit]
Description=Atlas Automation Hub Web / Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/usr/lib/atlas-hub/app
Environment="PATH=/usr/lib/atlas-hub/app/.venv/bin"
ExecStart=/usr/lib/atlas-hub/app/.venv/bin/gunicorn --worker-class=gevent --workers 1 --threads 30 --timeout 999999999 --access-logfile /var/log/atlas-hub/access.log --error-logfile /var/log/atlas-hub/error.log --capture-output --bind  unix:runner.sock --umask 007 runner:app

[Install]
WantedBy=multi-user.target
EOT
  cat <<EOT > /etc/systemd/system/atlas_hub_scheduler.service
[Unit]
Description=Atlas Automation Hub Web / Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/usr/lib/atlas-hub/app
Environment="PATH=/usr/lib/atlas-hub/app/.venv/bin"
ExecStart=/usr/lib/atlas-hub/app/.venv/bin/gunicorn --worker-class=gevent --workers 1 --threads 30 --timeout 999999999 --access-logfile /var/log/atlas-hub/access.log --error-logfile /var/log/atlas-hub/error.log --capture-output --bind  unix:scheduler.sock --umask 007 scheduler:app

[Install]
WantedBy=multi-user.target
EOT
}
