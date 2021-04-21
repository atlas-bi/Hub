#!/bin/bash
#
# This script should be run via curl:
#   bash -c "$(curl -kfsSL https://github.com/Riverside-Healthcare/extract_management.git)"
#
# or via wget:
#   bash -c "$(wget -O- https://github.com/Riverside-Healthcare/extract_management.git)"
#
# A server DNS can be specified by adding "DNS=none
# A different sql remote can be specified.
#

# get custom dns

DNS=none
REMOTE=https://github.com/Riverside-Healthcare/extract_management.git
ERROR=0

echo "$DNS"
echo "$REMOTE"

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

echo "${YELLOW}"
echo "

EEEEEEEEEEEEEEEEEEEEEE     MMMMMMMM               MMMMMMMM      222222222222222                 000000000
E::::::::::::::::::::E     M:::::::M             M:::::::M     2:::::::::::::::22             00:::::::::00
E::::::::::::::::::::E     M::::::::M           M::::::::M     2::::::222222:::::2          00:::::::::::::00
EE::::::EEEEEEEEE::::E     M:::::::::M         M:::::::::M     2222222     2:::::2         0:::::::000:::::::0
  E:::::E       EEEEEE     M::::::::::M       M::::::::::M                 2:::::2         0::::::0   0::::::0
  E:::::E                  M:::::::::::M     M:::::::::::M                 2:::::2         0:::::0     0:::::0
  E::::::EEEEEEEEEE        M:::::::M::::M   M::::M:::::::M              2222::::2          0:::::0     0:::::0
  E:::::::::::::::E        M::::::M M::::M M::::M M::::::M         22222::::::22           0:::::0     0:::::0
  E:::::::::::::::E        M::::::M  M::::M::::M  M::::::M       22::::::::222             0:::::0     0:::::0
  E::::::EEEEEEEEEE        M::::::M   M:::::::M   M::::::M      2:::::22222                0:::::0     0:::::0
  E:::::E                  M::::::M    M:::::M    M::::::M     2:::::2                     0:::::0     0:::::0
  E:::::E       EEEEEE     M::::::M     MMMMM     M::::::M     2:::::2                     0::::::0   0::::::0
EE::::::EEEEEEEE:::::E     M::::::M               M::::::M     2:::::2       222222        0:::::::000:::::::0
E::::::::::::::::::::E     M::::::M               M::::::M     2::::::2222222:::::2 ......  00:::::::::::::00
E::::::::::::::::::::E     M::::::M               M::::::M     2::::::::::::::::::2 .::::.    00:::::::::00
EEEEEEEEEEEEEEEEEEEEEE     MMMMMMMM               MMMMMMMM     22222222222222222222 ......      000000000


"

fmt_green "Thanks for installing Extract Management 2.0!"


fmt_blue "Verifying required packages are installed"
echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections

apt-get update -qq > /dev/null

command_install apt-utils
command_install pkg-config
command_install build-essential
command_install libssl-dev
command_install libffi-dev
command_install curl
command_install git
command_install wget
command_install libldap2-dev
command_install python3-dev
command_install python3-pip
command_install python3-setuptools
command_install unixodbc
command_install unixodbc-dev
command_install libpq-dev
command_install nginx
command_install sqlite3
command_install libsqlite3-0
command_install libsasl2-dev
command_install libxml2-dev
command_install libxmlsec1-dev
command_install libxmlsec1-dev
command_install redis-server
command_install ufw
command_install gnupg


fmt_blue "Updating timezone to CST"
sudo timedatectl set-timezone America/Chicago

fmt_blue "Setting up ufw port blocking"
sudo ufw default deny > /dev/null
sudo ufw allow ssh > /dev/null
sudo ufw allow "Nginx Full" > /dev/null
sudo ufw allow from 127.0.0.1 to any port 5001 > /dev/null
sudo ufw allow from 127.0.0.1 to any port 5002 > /dev/null
sudo ufw --force enable > /dev/null

# start redis
fmt_blue "Starting redis server"
$(which python3) -m pip install --disable-pip-version-check --quiet virtualenv setuptools wheel > /dev/null
sudo sed -i -e "s/supervised no/supervised systemd/g" /etc/redis/redis.conf > /dev/null
sudo systemctl enable redis-server > /dev/null
sudo systemctl start redis-server > /dev/null

# clear redis
# redis-cli FLUSHALL

# redis online?
fmt_green "Ping redis... $(redis-cli ping)?"

fmt_blue "Updating python settings"
export PYTHONDONTWRITEBYTECODE=1

fmt_blue "Installing SQL Server ODBC"
dpkg -s msodbcsql17 2>&1 |  grep -q 'is not installed' && fmt_install msodbcsql17 \
&& curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
&& curl -fsSL https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
&& sudo apt-get update --q \
&& sudo ACCEPT_EULA=Y apt-get install msodbcsql17 \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.bash_profile \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.bashrc \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.zshrc


HASHSCRIPT="
import hashlib
import time
print(hashlib.sha256(str(time.time()).encode('utf-8')).hexdigest()[:10])
"

HASH=$($(which python3) -c "$HASHSCRIPT")

fmt_green "Creating install directory /home/websites/em/$HASH"
mkdir -p "/home/websites/em/$HASH"
sudo chown -R webapp "/home/websites/em/$HASH"

cd "/home/websites/em/$HASH" || exit 1

sudo -u webapp git -c http.sslVerify=false clone --depth 1 "$REMOTE" . -q

fmt_green "${BOLD}Installing in /home/websites/em/$HASH"

# create python environment
fmt_blue "Creating python environment"
sudo -u webapp virtualenv -q --clear --no-periodic-update venv


# install Extract Management 2.0
fmt_blue "Installing dependencies"

# install poetry - the package manager
# shellcheck disable=SC1091
venv/bin/python -m pip install --disable-pip-version-check --quiet poetry
venv/bin/poetry config virtualenvs.create false
venv/bin/poetry install --no-dev --quiet
venv/bin/poetry add gunicorn --quiet
venv/bin/poetry add gevent --quiet

fmt_green "${UL}Env Info:"
fmt_yellow "$(venv/bin/poetry env info)"

# echo -e "\n${GREEN}Dep Info.${RESET}"
# echo -e "$(venv/bin/poetry show --tree)"

# make log files
fmt_blue "Creating gunicorn log files"
mkdir em_web/logs && touch em_web/logs/gunicorn-access.log && touch em_web/logs/gunicorn-error.log
mkdir em_runner/logs && touch em_runner/logs/gunicorn-access.log && touch em_runner/logs/gunicorn-error.log
mkdir em_scheduler/logs && touch em_scheduler/logs/gunicorn-access.log && touch em_scheduler/logs/gunicorn-error.log
sudo chmod 777 ./*/logs/*

# set up three sites - em_web, em_scheduler, and em_runner.

# copy model between apps
fmt_blue "Creating API db model"
cp em_web/model.py em_runner/model.py
cp em_web/model.py em_scheduler/model.py

# update hash in gunicorn files
fmt_blue "Updating gunicorn service files"
sed -i -e "s/hash/$HASH/g" ./*/publish/gunicorn.service

# move in three service files
fmt_blue "Installing gunicorn service files"
sudo mv "em_web/publish/gunicorn.service" "/etc/systemd/system/em_web.$HASH.service"
sudo mv "em_runner/publish/gunicorn.service" "/etc/systemd/system/em_runner.$HASH.service"
sudo mv "em_scheduler/publish/gunicorn.service" "/etc/systemd/system/em_scheduler.$HASH.service"

# start serice files and verify status
fmt_blue "Starting gunicorn services"
sudo systemctl start "em_web.$HASH.service" && sudo systemctl enable "em_web.$HASH.service" && sudo systemctl is-active "em_web.$HASH.service" | grep "inactive" > /dev/null && sudo systemctl status "em_web.$HASH.service" && ((ERROR++))
sudo systemctl start "em_runner.$HASH.service" && sudo systemctl enable "em_runner.$HASH.service" && sudo systemctl is-active "em_runner.$HASH.service" | grep "inactive" > /dev/null && sudo systemctl status "em_runner.$HASH.service" && ((ERROR++))
sudo systemctl start "em_scheduler.$HASH.service" && sudo systemctl enable "em_scheduler.$HASH.service" && sudo systemctl is-active "em_scheduler.$HASH.service" | grep "inactive" > /dev/null && sudo systemctl status "em_scheduler.$HASH.service" && ((ERROR++))

# update nginx service files
fmt_blue "Updating hash in nginx service files"
if [ "$DNS" = none ]; then
  sed -i -e "s/80/80 default_server/g" ./*/publish/nginx
else
  sed -i -e "s/dns/$DNS/g" ./*/publish/nginx
fi
sed -i -e "s/hash/$HASH/g" ./*/publish/nginx

fmt_blue "Installing nginx service files"
mv em_web/publish/nginx /etc/nginx/sites-available/em_web
mv em_runner/publish/nginx /etc/nginx/sites-available/em_runner
mv em_scheduler/publish/nginx /etc/nginx/sites-available/em_scheduler

fmt_blue "Starting nginx service files"
ln -s /etc/nginx/sites-available/em_web /etc/nginx/sites-enabled &> install.log
ln -s /etc/nginx/sites-available/em_runner /etc/nginx/sites-enabled &> install.log
ln -s /etc/nginx/sites-available/em_scheduler /etc/nginx/sites-enabled &> install.log

fmt_green "Reloading Nginx!"
sudo systemctl reload nginx
sudo systemctl is-active nginx | grep "inactive" > install.log && echo "${RED}!!!Failed to reload Nginx!!!${RESET}" && ((ERROR++))

# remove old gunicorn processes
fmt_blue "Removing old gunicorn processes"
sudo systemctl reset-failed
(cd /etc/systemd/system/ && ls em_*) | grep "em_*" | grep -v "em.*$HASH" | xargs -i sh -c 'sudo systemctl disable {} || true && sudo systemctl stop {} || true && sudo rm -f /etc/systemd/system/{}'
sudo systemctl reset-failed

# remove old instances of the website
fmt_blue "Removing old website instances"
(cd /home/websites/em/ && ls) | grep -v "$HASH" | xargs -i sh -c 'sudo rm -rf /home/websites/em/{} &>install.log'

# verify status
if [ "$DNS" = none ]; then
  DNS=none
fi

fmt_green "Checking online status - https://$DNS/login"

fmt_yellow "$(curl -sS "https://$DNS/login" --insecure -I)"

TITLE=$(curl -sS "https://$DNS/login" --insecure -so - | grep -iPo "(?<=<title>)(.*)(?=</title>)")
if [[ $TITLE == "Extract Management 2.0 - Login" ]] || [[ $TITLE == "Redirecting..." ]];
then
    fmt_green "Login page successfully reached!"
else
    fmt_error "Failed to reach login page! (Reached: $TITLE)"
    ((ERROR++))
fi;

fmt_blue "${UL}Debug Information"
echo -e "
${BLUE}${UL}Nginx${RESET}
${RED}sudo${RESET} tail -F /var/log/nginx/error.log
${RED}sudo${RESET} systemctl status ${GREEN}nginx${RESET}

${BLUE}${UL}Gunicorn${RESET}
${RED}sudo${RESET} journalctl -u ${GREEN}gunicorn${RESET}

# check service status
${RED}sudo${RESET} systemctl status ${GREEN}em_web.$HASH.service${RESET}
${RED}sudo${RESET} systemctl status ${GREEN}em_runner.$HASH.service${RESET}
${RED}sudo${RESET} systemctl status ${GREEN}em_scheduler.$HASH.service${RESET}

# read error logs
${RED}tail -300${RESET} /home/websites/em/${GREEN}$HASH${RESET}/em_web/logs/gunicorn-error.log${RESET}
${RED}tail -300${RESET} /home/websites/em/${GREEN}$HASH${RESET}/em_runner/logs/gunicorn-error.log${RESET}
${RED}tail -300${RESET} /home/websites/em/${GREEN}$HASH${RESET}/em_scheduler/logs/gunicorn-error.log${RESET}

# reload gunicorn processes
${RED}sudo${RESET} systemctl daemon-reload

${YELLOW}Finally, don't forget to login and reschedule tasks!${RESET}
"

# return error if there was an error
exit "$ERROR"
