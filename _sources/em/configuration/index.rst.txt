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


**************
Setting Up EM2
**************

.. toctree::
   :maxdepth: 1
   :titlesonly:
   :hidden:

   installation
   auth


Getting Started
~~~~~~~~~~~~~~~

EM2's configuration files are in three places:

* ``em_web/config.py``
* ``em_scheduler/config.py``
* ``em_runner/config.py``

These files need to be updated with parameters specific to you.

Creating Database
~~~~~~~~~~~~~~~~~

.. code:: python

    flask db init
    flask db migrate
    flask db upgrade
    flask cli seed

    # add demo data in needed
    # flask cli seed_demo

Tips
~~~~

If you use hostnames vs IP addresses in your config files be sure to update hosts file ``nano /etc/hosts`` to include the ip address of any internal domain hosts you will use. For example, LDAP server, GIT server, any databases you plan to query, etc.
