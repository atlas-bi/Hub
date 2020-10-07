<!-- 

	Extract Management 2.0
	Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <https://www.gnu.org/licenses/>. 

-->

# Extract Management 2.0

Extract Management 2.0 is a task scheduling tool intended to be used with getting data from a source and depositing it in a destination, primarily sql queries to SFTP servers.

The app is designed to be able to run tasks at any time/ on any schedule.

> :point_right: **[Live Demo](https://extract-management.herokuapp.com) - free hosting.. allow 30 seconds to start up app.**

## Run Extract Management 2.0 Docker Image

> :point_right: **[Extract Management Docker Image with Docker](https://hub.docker.com/r/christopherpickering/extract_management)**

### Running in [Docker Sandbox](https://labs.play-with-docker.com/)

1. Click "start"
2. Click "Settings" > 1 Manager and 1 Worker
3. Click on the Manager instance. Atlas is large and doesn't run in the worker.
4. Paste in ```docker run -i -t -p 5001:5001 -e PORT=5001  -u 0 christopherpickering/extract_management:latest
```
5. Wait about 1-2 mins for app to download and startup. Output will say ```Now listening on: http://[::]:5001``` when ready.
6. Click "Open Port" and type ```5001```
7. App will open in new tab. The URL should be valid for 3-4 hrs.

### Running Locally from Dockerhub
App can be run locally with our public docker image -
```sh
docker run -i -t -p 5001:5001 -e PORT=5001  -u 0 christopherpickering/extract_management:latest

```

### Building Your Own Image

```sh
# clone repository
docker build  --tag em .
docker run -i -t -p 5001:5001 -e PORT=5001  -u 0 em:latest
# web app will be running @ http://localhost:5001
```

## Run Extract Management 2.0 in Development Mode

### Linux Alpine Setup

#### Windows Hosts
If using a windows host you can find a wsl for Alpine Linux here: https://github.com/yuk7/AlpineWSL

I have found that if windows crashes and reboots your Alpine wsl will be hosted and you need to delete and reinstall. When deleteing, be sure and remove the registry key for it here: ```Computer\HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Lxss\<alpine>```

    Note: you may need to change the "Flags" in registry from 0 to 7 in order to mount drives. (Computer\HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Lxss\<alpine>\Flags)
    Changing this flag auto mounts the wsl into your home directory. 

#### Mac Hosts
If using a Mac host you can use virtualbox and install Alpine Linux with this tutorial: https://wiki.alpinelinux.org/wiki/Install_Alpine_on_VirtualBox

To enable shared folders with a VirtualBox host: https://wiki.alpinelinux.org/wiki/VirtualBox_shared_folders

We do not use virtual environments in Alpine, but install packages globally as Alpine is a one use disposable setup.

In the network settings > advanced enable port forwarding from a host port (2222 for example) to guest port 22. Then you can access the box through ssh: <user>@localhost:2000
	
#### Running Alpine in a Virtual Box Machine

After install of Alpine, add a new user for ssh connections.
```sh
adduser me
```

After ssh, change user back to root to be able to access/edit files

```sh
su - root
```

#### Enable zsh & oh-my-zsh shell (makes shell easier to use)

```sh
apk add --no-cache curl git nano zsh
git config --global http.sslVerify false
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
# if curl does not succeed, try wget.
sh -c "$(wget -O- https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# edit settings
nano /etc/passwd
# edit first line with "ash" to be "zsh"
```

##### Mount Local file system
In virtualbox settings add in a shared folder, then run these commands in the virtual machine to access it.

```sh
modprobe -a vboxsf
mount -t vboxsf rmc /mnt/outside
cd /mnt/outside

# to make life easier, save command to alias
nano ~/.zshrc

# past into alias section
alias my_mnt="mount -t vboxsf rmc /mnt/outside"

# then when loging into alpine run the command or just run "my_mnt" after ssh'ing into the machine.
```

#### Adding alias
```sh
nano ~/.zshrc
# scroll to end.. add: (no spaces around "="!!)
alias gs="git status"
alias gp="git push"
alias gc="git add . && git commit -m "
alias act="source venv/bin/activate"
alias dact="deactivate"
alias em="black -q . && export FLASK_ENV=development && export FLASK_DEBUG=1 && export FLASK_APP=em && flask run -h 0.0.0.0"
alias em_db_sqlite="rm jobs.sqlite || true && rm em.sqlite || true && rm -rf migrations || true && python manage.py db init && python manage.py db migrate && python manage.py db upgrade && sqlite3 em.sqlite '.read seed.sql'"

# save then activate
source ~/.zshrc
```

#### Add packages needed for install and setup.
```sh
ash
apk add --no-cache python3 build-base openldap-dev python3-dev tzdata libffi-dev openssl-dev sqlite unixodbc-dev postgresql-dev
cp /usr/share/zoneinfo/America/Chicago /etc/localtime && echo "America/Chicago" > /etc/timezone
apk del tzdata

export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
python3 -m ensurepip
pip3 install --no-cache --upgrade pip setuptools wheel
zsh
# any installs fail when fetching packages? clear cache and try again.
```

#### Git settings
```sh
git config --global http.sslVerify false # if your git repo location is insecure :)
git config --global credential.helper store
git config --global core.editor "nano"
git config --global user.name "Your Name"
git config --global user.email "your@email.address"
```

#### Install other reqirements
```sh
# to install from package
export FLASK_ENV=development && export FLASK_DEBUG=1 && export FLASK_APP=em
pip3 install -e .
```

#### Connect to MSSQL

https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15#alpine17](Ref

```sh
curl -k -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.6.1.1-1_amd64.apk

apk add --allow-untrusted msodbcsql17_17.6.1.1-1_amd64.apk
```

Finally, update hosts file ```nano /etc/hosts``` to include the ip address of any internal domain hosts you will use.
For example, LDAP server, GIT server, any databases you plan to query, etc. Alpine Linux in virtual box doesn't pick up the dns nicely.

#### Run

```sh
flask run
# or preferably, use the alias we have already created
em
```

## Database Setups and Migrations

There are two main databases. One for the webapp data and another for the job scheduler. The job scheduler db is automatically created, so we are only concerned with building the webapp db.

We've already created a nice alias to create an sqlite db and seed it. Check config.py first to be sure you are editing the correct db before running commands.
```sh
# create db's
em_db_sqlite
```

You can do it manually like so -

```sh
python manage.py db init # only to create the db
python manage.py db migrate
python manage.py db upgrade
```

After database creation some data must be populated.

Job Types
```sh
#for sqlite
sqlite3 em.sqlite ".read seed.sql"

```

So, a full command to create the database and seed would look something like this:
```sh
rm jobs.sqlite || true && rm em.sqlite || true && rm -rf migrations || true && python manage.py db init && python manage.py db migrate && python manage.py db upgrade && sqlite3 em.sqlite '.read seed.sql'
```

## How Login Works

Login is done through LDAP and follows this basic process
	Note: the python package python-simpleldap has been customized slightly to work with RMC's ldap setup.

1. config.py file holds the general connection info. A connection to the ldap server is made with the user credentials supplied in the config file.
2. Once a connection is established and a user attempts to access the site the simpleldap package first verifies that the user exists, by doin a search for the user. If the user exists we save their details and groups.
3. If the user exists then we attempt to log them in.. this returns true if they had a valid username/pass.
4. Finally, as this site is restricted to Analytics group users, we only allow users that have the "Analytics" group on their profile.

	Note: once logged in the user_id is kept in the server "session". When a user logs out we just drop the user_id from the session.

## Connecting to SQLite DB to view jobs

Open sqlite3.exe, or, run "sqlite3" in terminal... get a nice font there ;)

```sh
# help
.help

# open db
.open jobs.sqlite

# list tables
.tables
```
```sql
-- view jobs
select * from apscheduler_jobs;
```

## Data Flow

### Project Creation

Project name and schedule are created > tasks can be added to the project. 

Task are completely independent, the order of tasks is not respected and tasks may run in parallel. The purpose of allowing multiple tasks is to keep a clean grouping of tasks that belong to the same data project.

The tasks in a job can indivitually be started or stopped.


## Programming

### Javascript 
Hslint is the default linter.

### Python
Code formatted with Black and linted with pylint.

## How the App handles data
As code is run/data collected, etc, temporary files are used on the server. They reside in the location ```em/em/temp/<project name>/<task name>/<run id>/etc``` and are generally removed immediatly after their usefulness ends.

## Publishing
The app can be published to your webserver using python fabric module over an ssh connection. We are using Ubuntu Server 20, for other servers you may need to tweak the file slightly.

All publishing docs should be kept in the /publish folder. Contents should include:
* cert.crt (certificate)
* cert.key (cert key)
* fabfile.py (used to actually do the publishing)
* gunicorn.service (template file used to create a gunicorn service during publish)
* nginx (template file used to create a nginx service during publish)

The publish script can be run -
```sh
cd publish && fab -H user@host_ip --prompt-for-login-password --prompt-for-sudo-password \
    publish && cd ..
```

or easier, add an alias!
```sh
nano ~/.zshrc
# add
alias pub="cd publish && fab -H <user>@<host_ip> --prompt-for-login-password --prompt-for-sudo-password publish && cd .."
# and run 
pub
```

## Webserver Info

Currently ApScheduler must run on a single worker or tasks will be duplicated. We wait for [version 4](https://github.com/agronholm/apscheduler/issues/256) which should allow multiple workers.

Because of this, we need to allow the worker to stay alive longer than our longest running task.

### Nginx 

Update server Nginx params:
```sh
# open nginx config
sudo nano /etc/nginx/nginx.conf

# add these in the http secion. all for good luck...
fastcgi_connect_timeout 999s;
proxy_connect_timeout 999s;
proxy_read_timeout 999s;
```

### Gunicorn

We must only have 1 worker. It seems that with gevent we have the most success. The timeout must be longer than the longest running task. It make sence to match to Nginx timeout.

--workers 1
--timeout 999


## Credits

Atlas was created by the Riverside Healthcare Analytics team -

* Paula Courville
* [Darrel Drake](https://www.linkedin.com/in/darrel-drake-57562529)
* [Dee Anna Hillebrand](https://github.com/DHillebrand2016)
* [Scott Manley](https://github.com/Scott-Manley)
* [Madeline Matz](mailto:mmatz@RHC.net)
* [Christopher Pickering](https://github.com/christopherpickering)
* [Dan Ryan](https://github.com/danryan1011)
* [Richard Schissler](https://github.com/schiss152)
* [Eric Shultz](https://github.com/eshultz)

