|python-version| |travis| |codecov| |codacy| |codeql| |climate| |github|

Atlas Automation Hub
====================

.. image:: https://www.atlas.bi/static/img/automation-hub/dashboard.png
  :alt: Demo Image
  :width: 100%

Atlas Automation Hub is a task scheduling tool for getting data from a source and depositing it in a destination - sql servers to SFTP servers.

Tasks can run at any time and on any schedule.

Possibilities are almost unlimited....

- Run .bat files on windows servers over ssh
- Read, modify and resend files over FPT or SFTP
- ZIP and send data
- Run raw python code to process data and send
- Run code from FTP/SFTP/SAMB or web source
- Send output data embeded or attached to email
- Parameterize sql on the project or task leve
- Parameterize file names with date parameters
- Export data as text, csv, excel, delimited, or as a blob
- Encrypt data before sending
- Pull and send data from FTP/SFTP/SAMB/SSH
- Run SSH commands to monitor remote servers

Documentation
-------------

Read the `documentation <https://www.atlas.bi/docs/automation-hub/>`_.

Demo
----

Try out the `demo <https://atlas-hub.atlas.bi>`_!


Run from Source
~~~~~~~~~~~~~~~

Atlas Automation Hub can be run locally. We use pyenv and poetry to manage the project dependencies. Assuming you will too -

.. code:: sh

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

Finally, to run the three site, you will need to run each command in a separate termimal session:

.. code:: sh

    FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=web && flask run
    FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=scheduler && flask run --port=5001
    FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=runner && flask run --port=5002


Credits
-------

Atlas was created by the Riverside Healthcare Analytics team. See the `credits <https://www.atlas.bi/about/>`_ for more details.


.. |python-version| image:: https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9-blue
   :target: https://github.com/atlas-bi/atlas-automation-hub

.. |travis| image:: https://app.travis-ci.com/atlas-bi/atlas-automation-hub.svg?branch=main
    :target: https://app.travis-ci.com/atlas-bi/atlas-automation-hub

.. |codecov| image:: https://codecov.io/gh/atlas-bi/atlas-automation-hub/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/atlas-bi/atlas-automation-hub

.. |codacy| image:: https://app.codacy.com/project/badge/Grade/4fcece7632434b7a98902bc1c02fed80
   :target: https://www.codacy.com/gh/atlas-bi/atlas-automation-hub/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=atlas-bi/atlas-automation-hub&amp;utm_campaign=Badge_Grade

.. |climate| image:: https://api.codeclimate.com/v1/badges/269dcafa25cf15a571b3/maintainability
   :target: https://codeclimate.com/github/atlas-bi/atlas-automation-hub/maintainability
   :alt: Maintainability

.. |codeql| image:: https://github.com/atlas-bi/atlas-automation-hub/actions/workflows/quality.yml/badge.svg
   :target: https://github.com/atlas-bi/atlas-automation-hub/actions/workflows/quality.yml
   :alt: CodeQL

.. |github| image:: https://github.com/atlas-bi/atlas-automation-hub/workflows/CI/badge.svg
   :target: https://github.com/atlas-bi/atlas-automation-hub/actions
