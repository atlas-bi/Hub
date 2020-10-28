"""
    Extract Management 2.0 Publish Script

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

"""

import hashlib
import time
from fabric import task
from settings import config


@task
def publish(conn):

    """
    run by:

    cd publish && fab -H user@host_ip --prompt-for-login-password --prompt-for-sudo-password \
    publish && cd ..

    to monitor online status of site
    watch -n.1 curl -Is host_ip | grep HTTP

    Params
    git=/url/to/git/repo
    site_name
    server_name

    About
    each publish will create a new instance of the website + gunicorn. The new website will be
    started, the nginx config reloaded, and then the old gunicorn processes will be ended and
    removed. Finally, old code is removed.

    ##

    Never do migrations on the web server :)

    ##

    """

    git = config["git_url"]
    site_name = config["site_name"]
    server_name = config["server_name"]
    dns_name = config["dns_name"]

    # hash is used to identify current publish.
    my_hash = hashlib.sha256()
    my_hash.update(str(time.time()).encode("utf-8"))
    my_hash = my_hash.hexdigest()[:10]

    conn.run(
        "mkdir /home/websites/"
        + site_name
        + "-"
        + my_hash
        + " &&\
  cd /home/websites/"
        + site_name
        + "-"
        + my_hash
        + " &&\
  git -c http.sslVerify=false clone --depth 1 "
        + git
        + " . -q && \
  rm -rf .git &&\
  virtualenv -q -p=/usr/bin/python3.8 --clear --pip=20.2.3 --no-periodic-update venv && source venv/bin/activate && pip install -q -e . && pip install -q gunicorn && pip install -q gevent &&\
  deactivate && mkdir log && touch log/gunicorn-access.log && touch log/gunicorn-error.log"
    )

    # setup and start gunicorn service
    conn.run(
        "sed -i -e 's/site-name/"
        + site_name
        + "-"
        + my_hash
        + "/g' /home/websites/"
        + site_name
        + "-"
        + my_hash
        + "/publish/gunicorn.service"
    )
    conn.run(
        "sed -i -e 's/server-name/"
        + server_name
        + "/g' /home/websites/"
        + site_name
        + "-"
        + my_hash
        + "/publish/gunicorn.service"
    )
    conn.sudo(
        "mv /home/websites/"
        + site_name
        + "-"
        + my_hash
        + "/publish/gunicorn.service /etc/systemd/system/"
        + site_name
        + "-"
        + my_hash
        + ".service"
    )
    conn.sudo("systemctl start " + site_name + "-" + my_hash)
    conn.sudo("systemctl enable " + site_name + "-" + my_hash)
    # check gunicorn status
    conn.sudo("systemctl status " + site_name + "-" + my_hash + ".service")

    # update and reload nginx
    # nginx logs sudo tail -F /var/log/nginx/error.log
    conn.run(
        "sed -i -e 's/dns-name/"
        + dns_name
        + "/g' /home/websites/"
        + site_name
        + "-"
        + my_hash
        + "/publish/nginx"
    )
    conn.run(
        "sed -i -e 's/site-name/"
        + site_name
        + "-"
        + my_hash
        + "/g' /home/websites/"
        + site_name
        + "-"
        + my_hash
        + "/publish/nginx"
    )
    conn.run(
        "sed -i -e 's/server-name/"
        + server_name
        + "/g' /home/websites/"
        + site_name
        + "-"
        + my_hash
        + "/publish/nginx"
    )
    conn.run(
        "sed -i -e 's/app-name/"
        + site_name
        + "/g' /home/websites/"
        + site_name
        + "-"
        + my_hash
        + "/publish/nginx"
    )
    conn.sudo(
        "mv /home/websites/"
        + site_name
        + "-"
        + my_hash
        + "/publish/nginx /etc/nginx/sites-available/"
        + site_name
    )
    conn.sudo(
        "ln -s /etc/nginx/sites-available/"
        + site_name
        + " /etc/nginx/sites-enabled || true"
    )
    conn.sudo("systemctl reload nginx")

    # cleanup old gunicorn processes
    conn.sudo("systemctl reset-failed")
    print(
        'cd /etc/systemd/system && ls | grep "^'
        + site_name
        + '\\-.*" | grep -v "'
        + site_name
        + "-"
        + my_hash
        + '.service"'
    )
    services = str(
        conn.run(
            'cd /etc/systemd/system && ls | grep "^'
            + site_name
            + '\\-.*" | grep -v "'
            + site_name
            + "-"
            + my_hash
            + '.service"'
        )
    ).split("\n")
    if services:
        for service in services[2:-2]:
            conn.sudo(
                "systemctl status "
                + service
                + " |  sed -n 's/.*Main PID: \\(.*\\)$/\\1/g p' | cut -f1 -d' ' "
                + "| xargs kill -TERM || true"
            )
            # wait 10 seconds for processes to stop and remove old processes
            time.sleep(10)
            conn.sudo("systemctl disable " + service)
            conn.sudo("systemctl stop " + service)
            conn.sudo("rm /etc/systemd/system/" + service + " || true")

    # cleanup and old services
    conn.sudo("systemctl reset-failed")
    # guncorn logs sudo journalctl -u gunicorn

    # remove old code
    conn.run(
        "cd /home/websites && ls |grep '"
        + site_name
        + "-*' | grep -v '"
        + site_name
        + "-"
        + my_hash
        + "*' | xargs rm -rf || true"
    )

    # check if online
    conn.run("curl " + server_name)
    print("publish to " + server_name + " is complete.")

    print(
        """emergency restarts

# nginx logs
sudo tail -F /var/log/nginx/error.log
# guniforn logs
sudo journalctl -u gunicorn
sudo systemctl restart """
        + site_name
        + "-"
        + my_hash
        + """.service
sudo systemctl daemon-reload
sudo systemctl restart gunicorn.socket """
        + site_name
        + "-"
        + my_hash
        + """.service
sudo nginx -t && sudo systemctl restart nginx

Finally, don't forget to login and reschedule tasks!
"""
    )
