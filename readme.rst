..
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



|python-version| |travis| |codecov| |codacy| |codeql| |climate| |github|

Extract Management 2.0
======================

.. image:: images/em2.png
  :alt: Demo Image
  :width: 100%

Extract Management 2.0 is a task scheduling tool for getting data from a source and depositing it in a destination - sql servers to SFTP servers.

Tasks can run at any time and on any schedule.


Documentation
-------------

Check out our `documentation site <https://docs.extract.management>`_.

Demo
----

Checkout the `demo site <https://extract-management.herokuapp.com>`_!

Run with Docker
~~~~~~~~~~~~~~~

Or, you can run your own docker image:

.. code:: sh

    docker run -i -t -p 5003:5003 -e PORT=5003 -u 0 christopherpickering/extract_management:latest
    # access on http://localhost:5003


Run from Source
~~~~~~~~~~~~~~~

EM2 can be run locally. We use pyenv and poetry to manage the project dependencies. Assuming you will too -

.. code:: sh

    pyenv local 3.9.0
    poetry install

    # have you already created a database "em_web_dev" and updated the config files?
    FLASK_APP=em_web
    flask db init
    flask db migrate
    flask db upgrade
    flask cli seed
    # if you want some basic demo information added
    flask cli seed_demo

Finally, to run the three site, you will need to run each command in a separate termimal session:

.. code:: sh

    FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=em_web && flask run
    FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=em_scheduler && flask run --port=5001
    FLASK_ENV=development && FLASK_DEBUG=1 && FLASK_APP=em_runner && flask run --port=5002


Credits
-------

Atlas was created by the Riverside Healthcare Analytics team -

- Paula Courville
- `Darrel Drake <https://www.linkedin.com/in/darrel-drake-57562529>`_
- `Dee Anna Hillebrand <https://github.com/DHillebrand2016>`_
- `Scott Manley <https://github.com/Scott-Manley>`_
- `Madeline Matz <mailto:mmatz@RHC.net>`_
- `Christopher Pickering <https://github.com/christopherpickering>`_
- `Dan Ryan <https://github.com/danryan1011>`_
- `Richard Schissler <https://github.com/schiss152>`_
- `Eric Shultz <https://github.com/eshultz>`_

.. |python-version| image:: https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9-blue
   :target: https://analyticsgit.riversidehealthcare.net/extract-management/extract-management-site/-/commits/master

.. |travis| image:: https://travis-ci.com/Riverside-Healthcare/extract_management.svg?branch=main
    :target: https://travis-ci.com/Riverside-Healthcare/extract_management

.. |codecov| image:: https://codecov.io/gh/Riverside-Healthcare/extract_management/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/Riverside-Healthcare/extract_management

.. |codacy| image:: https://app.codacy.com/project/badge/Grade/37f4bf4e23c14d928ee0effde32cc5f1
   :target: https://www.codacy.com/gh/Riverside-Healthcare/extract_management/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Riverside-Healthcare/extract_management&amp;utm_campaign=Badge_Grade

.. |climate| image:: https://api.codeclimate.com/v1/badges/7dffbd981397d1152b59/maintainability
   :target: https://codeclimate.com/github/Riverside-Healthcare/extract_management/maintainability
   :alt: Maintainability

.. |codeql| image:: https://github.com/Riverside-Healthcare/extract_management/workflows/CodeQL/badge.svg
   :target: https://github.com/Riverside-Healthcare/extract_management/actions/workflows/codeql-analysis.yml
   :alt: CodeQL

.. |github| image:: https://github.com/Riverside-Healthcare/extract_management/workflows/CI/badge.svg
   :target: https://github.com/Riverside-Healthcare/extract_management/actions
