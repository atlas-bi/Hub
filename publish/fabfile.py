"""Extract Management 2.0 Publish Script."""
# Extract Management 2.0
# Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from fabric import task
from settings import config


@task
def publish(conn):
    """Remotly publish Extract Management 2.0.

    :param conn: connection to deploy to

    Deploy Extract Management 2.0 by running:

    .. code-block:: console

        cd publish && fab -H user@host_ip --prompt-for-login-password --prompt-for-sudo-password \
        publish && cd ..

    To monitor online status of site while publishing

    .. code-block:: console

        watch -n.1 curl -Is host_ip | grep HTTP

    About
    Each publish will create a new instance of the website + gunicorn. The new website will be
    started, the nginx config reloaded, and then the old gunicorn processes will be ended and
    removed. Finally, old code is removed.

    """
    conn.sudo(
        'bash -c "$(curl -kfsSL -H "PRIVATE-TOKEN: %s" "%s")"'
        % (config["token"], config["sh"])
    )
