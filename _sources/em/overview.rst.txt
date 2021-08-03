..
    Atlas of Information Management
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

*************
About the App
*************

EM2 is a three part server:

- web app
- scheduler
- job runner

EM2 runs with Nginx + Gunicorn. Three individual web services are created, the web app is the public web site and the other two (scheduler and runner) are internal API's running on the web server.

Prerequisites
~~~~~~~~~~~~~

- Currently EM2 is setup to install on an Ubuntu server, however with a few tweaks to the install script it will work well on most Linux.
- curl or wget should be installed
- Ideally, you will have your own git repository, holding updated config files, and will publish from there.


Data Flow
~~~~~~~~~

Project name and schedule are created > tasks can be added to the project.

Task are completely independent, the order of tasks is not respected and tasks may run in parallel. The purpose of allowing multiple tasks is to keep a clean grouping of tasks that belong to the same data project.

The tasks in a job can individually be started or stopped.

Webserver Info
~~~~~~~~~~~~~~

EM2 uses three web services for a few reasons -

- Splitting the UI from the running tasks improves the user experience
- The scheduler must run on only 1 web worker, while we would like as many workers as possible for the runner.
- API's are cool.

In the EM2 admin screen there is an option to retart the web services. For this option to work you may need to give you webapp user sudo permission, or:

.. code:: sh

    sudo visudo

    # add this line to the end.. assuming the webapp usergroup is "webapp"
    %webapp ALL=NOPASSWD: /bin/systemctl daemon-reload
    %webapp ALL=NOPASSWD: /bin/systemctl restart *

If you will have "long running" tasks, it may be wise to increase the nginx timeout. (Gunicorn timeouts are already increased in the app install files.)

.. code:: sh

    # open nginx config
    sudo nano /etc/nginx/nginx.conf

    # add these in the http secion. all for good luck...
    fastcgi_connect_timeout 999s;
    proxy_connect_timeout 999s;
    proxy_read_timeout 999s;
