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
Installation
*************


An install script is provided to easily install EM2 onto your Ubuntu server. Update the ``publish/install.sh`` file "dns" value to be the dns of your server, and the "remote" to point to your repo path. If you plan to use ssl you can add the certs into the ``publish`` folder as well. Use names "cert.crt" and "cert.key".

The publish takes place over SSH from a git server. It is possible to use an accesskey when publishing from fabric.

Update username and hostname with your planned login. Commands require sudo. ``sudo bash...``

+----------+----------------------------------------------------------------------------------------------------------------------------------+
| Method   | Command                                                                                                                          |
+==========+==================================================================================================================================+
| fabric   | ``cd publish && fab publish && cd ..``                                                                                           |
+----------+----------------------------------------------------------------------------------------------------------------------------------+
| curl     | ``bash -c "$(curl -kfsSL https://raw.githubusercontent.com/Riverside-Healthcare/extract_management/main/publish/install.sh)"``   |
+----------+----------------------------------------------------------------------------------------------------------------------------------+
| wget     | ``bash -c "$(wget -O- https://raw.githubusercontent.com/Riverside-Healthcare/extract_management/main/publish/install.sh)"``      |
+----------+----------------------------------------------------------------------------------------------------------------------------------+

After cloning the repository the ``install.sh`` script will install all packages necessary to start up the app.
