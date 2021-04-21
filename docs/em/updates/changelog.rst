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

*********
Changelog
*********

Version 2021.04.1
-----------------

- Added SAML auth as default
- Changed to use flask-login for user session
- Increased test cov to 60%
- Hide nav when showing 400/500 errors
- Fixed bug where ``errored > run all now`` button was not working
- Fixed bug with screen resize when changing tabs
- Updated project page to have logs on tab 2
- Fixed bug with adding duplicate SMB connections when creating a new connection
- Added option to include custom line ending in output text files
- Added background task for maintenance


Version 2021.03.1
-----------------

- Rewrote Scheduler API as flask application factory
- Changed task enable/disable to a toggle
- Fixed bug that didn't allow py scripts from a git url
- Fixed bug that was hiding organization input on new ssh tasks
- Updated to latest version of SQL Alchemy
- Added in run duration
- Added file checksum to file logs
- Added option to rerun all running tasks from dashboard
- Added logging of current row count of exports from SQL Server queries
- Fixed bug with parsing sql queries to remove "go" command
- Added basic search
- Added option to encrypt files with gpg keys
- Fixed bug resending blanks files to SFTP servers
- Fixed display issue with cron schedules on projects
- Allow gitlab/hub "blob" urls as well as "raw" urls
- Added ability to auto retry extracts x number of times
- Fixed a few timezone bugs
- Fixed display issue with code previews
- Added option to embed output file in email vs sending as attachment
- Added option to connect to SFTP servers with SSH keys
- Added file streaming for large queries/files to reduce memory usage
- Fixed file size calculation
