

<h1 align="center">
    <br>
    <a href="https://www.atlas.bi">
        <img alt="atlas logo" src="https://raw.githubusercontent.com/atlas-bi/atlas-automation-hub/master/share/logo.png" width=520 />
    </a>
    <br>
</h1>

<h4 align="center">Atlas Automation Hub | A simple extract, batch job and script scheduler.</h4>

<p align="center">
    <a href="https://www.atlas.bi" target="_blank">Website</a> • <a href="https://atlas-hub.atlas.bi" target="_blank">Demo</a> • <a href="https://www.atlas.bi/docs/automation-hub/" target="_blank">Documentation</a> • <a href="https://discord.gg/hdz2cpygQD" target="_blank">Chat</a>
</p>

<p align="center">
Atlas Automation Hub is a task scheduling tool for getting data from a source and depositing it in a destination - sql servers to SFTP servers.
</p>

<p align="center">
    <a href="https://www.codacy.com/gh/atlas-bi/atlas-automation-hub/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=atlas-bi/atlas-automation-hub&amp;utm_campaign=Badge_Grade" target="_blank"><img alt="codacy badge" src="https://app.codacy.com/project/badge/Grade/4fcece7632434b7a98902bc1c02fed80" /></a>
<a href="https://codecov.io/gh/atlas-bi/atlas-automation-hub" target="_blank">
  <img alt="coverage badge" src="https://codecov.io/gh/atlas-bi/atlas-automation-hub/branch/main/graph/badge.svg"/>
</a>
<a href="https://github.com/atlas-bi/atlas-automation-hub/actions/workflows/test.yml" target="_blank"><img src="https://github.com/atlas-bi/atlas-automation-hub/actions/workflows/test.yml/badge.svg" /></a>
<a href="https://discord.gg/hdz2cpygQD"><img alt="discord chat" src="https://badgen.net/discord/online-members/hdz2cpygQD/" /></a>
<a href="https://github.com/atlas-bi/atlas-automation-hub/releases"><img alt="latest release" src="https://badgen.net/github/release/atlas-bi/atlas-automation-hub" /></a>
</p>

<p align="center">
    <img alt="demo" src="https://www.atlas.bi/static/img/automation-hub/dashboard.png" width=520 />
</p>

## :thinking: What Can It Do?

Tasks can run at any time and on any schedule.

Possibilities are almost unlimited....

- Run .bat files on windows servers over ssh
- Read, modify and resend files over FPT or SFTP
- ZIP and send data
- Run raw python code to process data and send
- Run code from FTP/SFTP/SAMB or web source
- Send output data embedded or attached to email
- Parameterize sql on the project or task level
- Parameterize file names with date parameters
- Export data as text, csv, excel, delimited, or as a blob
- Encrypt data before sending
- Pull and send data from FTP/SFTP/SAMB/SSH
- Run SSH commands to monitor remote servers


## :runner: Start It Up

Atlas Automation Hub can be run locally. We use pyenv and poetry to manage the project dependencies. Assuming you will too -

```bash
pyenv local 3.9.0
poetry install

# have you already created a database "atlas_hub_dev" and updated the config files?
FLASK_APP=web
flask db init
flask db migrate
flask db upgrade
flask cli seed
# if you want some basic demo information added
flask cli seed_demo
```

Finally, to run the three site, you will need to run each command in a separate termimal session:

```bash
FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=web && flask run
FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=scheduler && flask run --port=5001
FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=runner && flask run --port=5002
```

## :test_tube: Testing

Tests require a running `postgresql` and `redis` instances.

Start up a demo sql, sftp and ftp servers with docker:

```bash
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=@Passw0rd>" -p 1433:1433 --name sql1 -h sql1  -d mcr.microsoft.com/mssql/server:2017-latest
docker run -p 23:22 -d emberstack/sftp --name sftp
docker run -d --name ftpd_server -p 21:21 -p 30000-30009:30000-30009 -e FTP_USER_NAME=demo -e FTP_USER_PASS=demo -e FTP_USER_HOME=/home/demo -e "PUBLICHOST=localhost" -e "ADDED_FLAGS=-d -d" stilliard/pure-ftpd
```

Final, simply run the tests with `tox`.

## :rocket: Install

Atlas Hub is built for linux and only takes [three commands](https://www.atlas.bi/docs/automation-hub/install/) to install.

## :gift: Contributing

Contributions are welcome! Please open an [issue](https://github.com/atlas-bi/atlas-automation-hub/issues) describing an issue or feature.

This repository uses commitizen. Commit code changes for pr's with `npm run commit`.


## :trophy: Credits

Atlas was created by the Riverside Healthcare Analytics team. See the `credits <https://www.atlas.bi/about/>`_ for more details.

## :wrench: Tools

Special thanks to a few other tools used here.

<img src="https://badgen.net/badge/icon/gitguardian?icon=gitguardian&label" alt="gitguardian"> <img src="https://img.shields.io/badge/renovate-configured-green?logo=renovatebot" alt="renovate"> <a href="https://snyk.io/test/github/atlas-bi/atlas-automation-hub"><img src="https://snyk.io/test/github/atlas-bi/atlas-automation-hub/badge.svg" alt="snyk" /></a> <a href="https://sonarcloud.io/summary/new_code?id=atlas-bi_atlas-automation-hub"><img src="https://sonarcloud.io/api/project_badges/measure?project=atlas-bi_atlas-automation-hub&metric=alert_status" alt="quality gate sonar" /></a> <a href="http://commitizen.github.io/cz-cli/"><a src="https://img.shields.io/badge/commitizen-friendly-brightgreen.svg" alt="commitizen"></a>
<a href="https://github.com/semantic-release/semantic-release"><img src="https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg" alt="semantic-release" /></a>
