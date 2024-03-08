"""Run web tests.

.. code::

    poetry run pytest tests/ \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[2]) + "/scripts")
from database import get_or_create, seed  # isort:skip
