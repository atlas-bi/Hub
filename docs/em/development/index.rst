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

***********
Development
***********

EM2 is developed using python and a few helpful tools:

Primary Tools
-------------

- `Pyenv <https://github.com/pyenv/pyenv>`_ for managing python environments
- `Poetry <https://python-poetry.org>`_ for managing dependencies
- `Precommit <https://pre-commit.com>`_  for reformating code before committing
- `Tox <https://tox.readthedocs.io/en/latest/index.html>`_  running tests, verifying code


Precommit Setup
~~~~~~~~~~~~~~~

To setup precommit hooks:

.. code:: sh

    precommit install


Testing
~~~~~~~

Code (python/javascript/css/html) is all tested with tox:

.. code:: sh

    tox

Running Pytests
~~~~~~~~~~~~~~~

With Poetry:

.. code:: sh

    export FLASK_APP=em_web; export FLASK_ENV=test; poetry run python -m pytest --disable-warnings


With tox:

.. code:: sh

    tox -e clean,py39,cov

    # or 

    poetry run tox -e clean,py39,cov
