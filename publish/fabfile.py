"""Publish Script."""

from fabric import Config, Connection, task
from settings import config

# pylint: disable=W0105
"""
for debug:
import logging
logging.basicConfig(level=logging.DEBUG)
"""


@task
def publish(ctx):
    """Remotely deploy.

    Deploy by running:

    .. code-block:: console

        cd publish && fab publish && cd ..

    To monitor online status of site while publishing

    .. code-block:: console

        watch -n.1 curl -Is host_ip | grep HTTP

    About
    Each publish will create a new instance of the website + gunicorn. The new website will be
    started, the nginx config reloaded, and then the old gunicorn processes will be ended and
    removed. Finally, old code is removed.

    """
    connection_properties = {
        "host": config["host"],
        "user": config["user"],
        "config": Config(overrides={"sudo": {"password": config["pass"]}}),
        "connect_kwargs": {"password": config["pass"], "allow_agent": False},
    }
    # pylint: disable=R1704
    with Connection(**connection_properties) as ctx:
        ctx.sudo(
            'bash -c "$(curl -kfsSL -H "PRIVATE-TOKEN: %s" "%s")"'
            % (config["token"], config["sh"])
        )
