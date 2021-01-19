#!/bin/bash
# to run: bash install.sh <install hash> <dns>

HASH=$1
DNS=$2
RED='\e[1;31m'
GREEN='\e[1;32m'
YELLOW='\e[1;33m'
BLUE='\e[1;34m'
UL='\e[4m'
NC='\033[0m' # No Color
ERROR=0

echo -e "\n\n${YELLOW}"
echo "\
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

echo -e "\n\n${YELLOW}Thanks for installing Extract Management 2.0!${NC}"
echo -e "\n${GREEN}Running install as $(whoami) with hash $HASH${NC}"

echo -e "\n${BLUE}Installing packages${NC}"
echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections

apt-get update -qq > /dev/null
dpkg -s apt-utils 2>&1 |  grep -q 'is not installed' && echo "Installing apt-utils" && apt-get install -y -qq --no-install-recommends apt-utils > /dev/null
dpkg -s pkg-config 2>&1 |  grep -q 'is not installed' && echo "Installing pkg-config" && apt-get install -y -qq --no-install-recommends pkg-config > /dev/null
dpkg -s build-essential 2>&1 |  grep -q 'is not installed' && echo "Installing build-essential" && apt-get install -y -qq build-essential > /dev/null
dpkg -s libssl-dev 2>&1 |  grep -q 'is not installed' && echo "Installing libssl-dev" && apt-get install -y -qq libssl-dev > /dev/null
dpkg -s libffi-dev 2>&1 |  grep -q 'is not installed' && echo "Installing libffi-dev" && apt-get install -y -qq libffi-dev > /dev/null
dpkg -s curl 2>&1 |  grep -q 'is not installed' && echo "Installing curl" && apt-get install -y -qq curl > /dev/null
dpkg -s git 2>&1 |  grep -q 'is not installed' && echo "Installing git" && apt-get install -y -qq git > /dev/null
dpkg -s wget 2>&1 |  grep -q 'is not installed' && echo "Installing wget" && apt-get install -y -qq wget > /dev/null
dpkg -s libldap2-dev 2>&1 |  grep -q 'is not installed' && echo "Installing libldap2-dev" && apt-get install -y -qq libldap2-dev > /dev/null
dpkg -s python3-dev 2>&1 |  grep -q 'is not installed' && echo "Installing python3-dev" && apt-get install -y -qq python3-dev > /dev/null
dpkg -s python3-pip 2>&1 |  grep -q 'is not installed' && echo "Installing python3-pip" && apt-get install -y -qq python3-pip > /dev/null
dpkg -s python3-setuptools 2>&1 |  grep -q 'is not installed' && echo "Installing python3-setuptools" && apt-get install -y -qq python3-setuptoolsv > /dev/null
dpkg -s unixodbc 2>&1 |  grep -q 'is not installed' && echo "Installing unixodbc" && apt-get install -y -qq unixodbc > /dev/null
dpkg -s unixodbc-dev 2>&1 |  grep -q 'is not installed' && echo "Installing unixodbc-dev" && apt-get install -y -qq unixodbc-dev > /dev/null
dpkg -s nginx 2>&1 |  grep -q 'is not installed' && echo "Installing nginx" && apt-get install -y -qq nginx > /dev/null
dpkg -s sqlite3 2>&1 |  grep -q 'is not installed' && echo "Installing sqlite3" && apt-get install -y -qq sqlite3 > /dev/null
dpkg -s libsqlite3-0 2>&1 |  grep -q 'is not installed' && echo "Installing libsqlite3-0" && apt-get install -y -qq libsqlite3-0 > /dev/null
dpkg -s libsasl2-dev 2>&1 |  grep -q 'is not installed' && echo "Installing libsasl2-dev" && apt-get install -y -qq libsasl2-dev > /dev/null
dpkg -s libxml2-dev 2>&1 |  grep -q 'is not installed' && echo "Installing libxml2-dev" && apt-get install -y -qq libxml2-dev > /dev/null
dpkg -s libxmlsec1-dev 2>&1 |  grep -q 'is not installed' && echo "Installing libxmlsec1-dev" && apt-get install -y -qq libxmlsec1-dev > /dev/null
dpkg -s libxmlsec1-openssl 2>&1 |  grep -q 'is not installed' && echo "Installing libxmlsec1-openssl" && apt-get install -y -qq libxmlsec1-openssl > /dev/null
dpkg -s redis-server 2>&1 |  grep -q 'is not installed' && echo "Installing redis-server" && apt-get install -y -qq redis-server > /dev/null
dpkg -s ufw 2>&1 |  grep -q 'is not installed' && echo "Installing ufw" && apt-get install -y -qq ufw > /dev/null

echo -e "\n${BLUE}Update timezone.${NC}"
sudo set-timezone America/Chicago

echo -e "\n${BLUE}Disable Git SSL${NC}"
git config --global http.sslVerify false

# setup ufw
echo -e "\n${BLUE}Setup ufw port blocking${NC}"
sudo ufw default deny > /dev/null
sudo ufw allow ssh > /dev/null
sudo ufw allow "Nginx Full" > /dev/null
sudo ufw allow from 127.0.0.1 to any port 5001 > /dev/null
sudo ufw allow from 127.0.0.1 to any port 5002 > /dev/null
sudo ufw --force enable > /dev/null

# start redis
echo -e "\n${BLUE}Start redis server${NC}"
# enable systemd control
$(which python3) -m pip install --disable-pip-version-check --quiet virtualenv setuptools wheel > /dev/null
sudo sed -i -e "s/supervised no/supervised systemd/g" /etc/redis/redis.conf > /dev/null
sudo systemctl enable redis-server > /dev/null
sudo systemctl start redis-server > /dev/null
# clear redis
# redis-cli FLUSHALL

# redis online?
echo -e "\n${BLUE}Ping redis... online?${GREEN}"
redis-cli ping
echo -e "${NC}"

echo -e "\n${BLUE}Updating python settings${NC}"
export PYTHONDONTWRITEBYTECODE=1

# setup sql server
echo -e "\n${BLUE}Checking SQL Server ODBC${NC}"
dpkg -s msodbcsql17 2>&1 |  grep -q 'is not installed' && echo "Installing msodbcsql17" \
&& curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
&& curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
&& sudo apt-get update --q \
&& sudo ACCEPT_EULA=Y apt-get install msodbcsql17 \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.bash_profile \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.bashrc \
&& echo "export PATH=\"$PATH:/opt/mssql-tools/bin\"" >> ~/.zshrc

echo -e "\n${GREEN}${UL}Installing in /home/websites/em/$HASH${NC}\n"

# change dir
cd "/home/websites/em/$HASH" || exit

# create python environment
echo -e "${BLUE}Creating python environment.${NC}"

sudo -u webapp virtualenv -q --clear --no-periodic-update venv

# install Extract Management 2.0
# shellcheck disable=SC1091
echo -e "${BLUE}Installing deps.${NC}"

# install poetry - the package manager
# shellcheck disable=SC1091
source venv/bin/activate && python -m pip install --disable-pip-version-check --quiet poetry

# disable env creation
poetry config virtualenvs.create false

# install and list deps
venv/bin/poetry install --no-dev --quiet
venv/bin/poetry add gunicorn --quiet
venv/bin/poetry add gevent --quiet

echo -e "\n${GREEN}${UL}Env Info:${NC}"
echo -e "${YELLOW}$(venv/bin/poetry env info)${NC}\n"

# echo -e "\n${GREEN}Dep Info.${NC}"
# echo -e "$(venv/bin/poetry show --tree)"

# make log files
echo -e "${BLUE}Creating log files.${NC}"
mkdir em_web/logs && touch em_web/logs/gunicorn-access.log && touch em_web/logs/gunicorn-error.log
mkdir em_runner/logs && touch em_runner/logs/gunicorn-access.log && touch em_runner/logs/gunicorn-error.log
mkdir em_scheduler/logs && touch em_scheduler/logs/gunicorn-access.log && touch em_scheduler/logs/gunicorn-error.log
sudo chmod 777 ./*/logs/*

# set up three sites - em_web, em_scheduler, and em_runner.

# copy model between apps
cp em_web/model.py em_runner/model.py
cp em_web/model.py em_scheduler/model.py

# update hash in gunicorn files
echo -e "${BLUE}Updating hash in gunicorn service files.${NC}"
sed -i -e "s/hash/$HASH/g" ./*/publish/gunicorn.service

# move in three service files
echo -e "${BLUE}Installing gunicorn service files.${NC}"
sudo mv "em_web/publish/gunicorn.service" "/etc/systemd/system/em_web.$HASH.service"
sudo mv "em_runner/publish/gunicorn.service" "/etc/systemd/system/em_runner.$HASH.service"
sudo mv "em_scheduler/publish/gunicorn.service" "/etc/systemd/system/em_scheduler.$HASH.service"

# start serice files and verify status
echo -e "${BLUE}Starting gunicorn services.${NC}"
sudo systemctl start "em_web.$HASH.service" && sudo systemctl enable "em_web.$HASH.service" && sudo systemctl is-active "em_web.$HASH.service" | grep "inactive" > /dev/null && sudo systemctl status "em_web.$HASH.service" && ((ERROR++))
sudo systemctl start "em_runner.$HASH.service" && sudo systemctl enable "em_runner.$HASH.service" && sudo systemctl is-active "em_runner.$HASH.service" | grep "inactive" > /dev/null && sudo systemctl status "em_runner.$HASH.service" && ((ERROR++))
sudo systemctl start "em_scheduler.$HASH.service" && sudo systemctl enable "em_scheduler.$HASH.service" && sudo systemctl is-active "em_scheduler.$HASH.service" | grep "inactive" > /dev/null && sudo systemctl status "em_scheduler.$HASH.service" && ((ERROR++))

# update nginx service files
echo -e "${BLUE}Updating hash in nginx service files.${NC}"
sed -i -e "s/dns/$DNS/g" ./*/publish/nginx
sed -i -e "s/hash/$HASH/g" ./*/publish/nginx

# move in files. These will not have a hash and will replace old service files.
echo -e "${BLUE}Installing nginx service files.${NC}"
mv em_web/publish/nginx /etc/nginx/sites-available/em_web
mv em_runner/publish/nginx /etc/nginx/sites-available/em_runner
mv em_scheduler/publish/nginx /etc/nginx/sites-available/em_scheduler

# create symlinks in sites enabled to enable sites. bypass errors about already existing links
echo -e "${BLUE}Starting nginx service files.${NC}"
ln -s /etc/nginx/sites-available/em_web /etc/nginx/sites-enabled &> install.log
ln -s /etc/nginx/sites-available/em_runner /etc/nginx/sites-enabled &> install.log
ln -s /etc/nginx/sites-available/em_scheduler /etc/nginx/sites-enabled &> install.log

# reload nginx. all traffic will not be redirected to new gunicorn processes!
echo -e "${GREEN}Reloading Nginx!${NC}"
sudo systemctl reload nginx
sudo systemctl is-active nginx | grep "inactive" > install.log && echo "${RED}!!!Failed to reload Nginx!!!${NC}" && ((ERROR++))

# remove old gunicorn processes
echo -e "${BLUE}Removing old gunicorn processes.${NC}"
sudo systemctl reset-failed

(cd /etc/systemd/system/ && ls em_*) | grep "em_*" | grep -v "em.*$HASH" | xargs -i sh -c 'sudo systemctl disable {} || true && sudo systemctl stop {} || true && sudo rm -f /etc/systemd/system/{}'

sudo systemctl reset-failed

# remove old instances of the website
echo -e "${BLUE}Removing old website instances.${NC}"
(cd /home/websites/em/ && ls) | grep -v "$HASH" | xargs -i sh -c 'sudo rm -rf /home/websites/em/{} &>install.log'

# verify status
echo -e "\n${GREEN}Checking online status - https://$DNS/login${NC}\n"

echo -e "${YELLOW}$(curl -sS "https://$DNS/login" --insecure -I)${NC}"

TITLE=$(curl -sS "https://$DNS/login" --insecure -so - | grep -iPo "(?<=<title>)(.*)(?=</title>)")
if [[ $TITLE == "Extract Management 2.0 - Login" ]];
then
    echo -e "\n${GREEN}Login page successfully reached!${NC}\n"
else
    echo -e "\n${RED}Failed to reach login page! (Reached: $TITLE)${NC}\n"
    ((ERROR++))
fi;

echo -e "\n${BLUE}${UL}Debug Information${NC}

${BLUE}${UL}Nginx${NC}
${RED}sudo${NC} tail -F /var/log/nginx/error.log
${RED}sudo${NC} systemctl status ${GREEN}nginx${NC}

${BLUE}${UL}Gunicorn${NC}
${RED}sudo${NC} journalctl -u ${GREEN}gunicorn${NC}

# check service status
${RED}sudo${NC} systemctl status ${GREEN}em_web.$HASH.service${NC}
${RED}sudo${NC} systemctl status ${GREEN}em_runner.$HASH.service${NC}
${RED}sudo${NC} systemctl status ${GREEN}em_scheduler.$HASH.service${NC}

# read error logs
${RED}tail -300${NC} /home/websites/em/${GREEN}$HASH${NC}/em_web/logs/gunicorn-error.log${NC}
${RED}tail -300${NC} /home/websites/em/${GREEN}$HASH${NC}/em_runner/logs/gunicorn-error.log${NC}
${RED}tail -300${NC} /home/websites/em/${GREEN}$HASH${NC}/em_scheduler/logs/gunicorn-error.log${NC}

# reload gunicorn processes
${RED}sudo${NC} systemctl daemon-reload

${YELLOW}Finally, don't forget to login and reschedule tasks!${NC}
"

# return error if there was an error
exit "$ERROR"

