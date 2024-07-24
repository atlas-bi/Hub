"""Test system.

run with::

   poetry run pytest runner/tests/test_scripts_system.py \
       --cov --cov-append --cov-branch --cov-report=term-missing --disable-warnings


   poetry run pytest runner/tests/test_scripts_system.py::test_monitor_fail \
       --cov --cov-append --cov-branch  --cov-report=term-missing --disable-warnings

"""

import pytest
from pytest import fixture

from runner.scripts.em_system import system_monitor


def test_monitor(client_fixture: fixture) -> None:
    system_monitor()


def test_monitor_fail_disk(client_fixture: fixture) -> None:
    # override disk space
    old_config = client_fixture.application.config["MIN_DISK_SPACE"]
    client_fixture.application.config["MIN_DISK_SPACE"] = 10000000000000000000

    with pytest.raises(ValueError) as e:
        system_monitor()
        assert "System is below minimum disk space threshold." in e

    client_fixture.application.config["MIN_DISK_SPACE"] = old_config


def test_monitor_fail_cpu(client_fixture: fixture) -> None:
    old_config = client_fixture.application.config["MIN_FREE_CPU_PERC"]
    client_fixture.application.config["MIN_FREE_CPU_PERC"] = 100

    with pytest.raises(ValueError) as e:
        system_monitor()
        assert "System is over maximum cpu threshold." in e

    client_fixture.application.config["MIN_FREE_CPU_PERC"] = old_config


def test_monitor_fail_mem(client_fixture: fixture) -> None:
    old_config = client_fixture.application.config["MIN_FREE_MEM_PERC"]
    client_fixture.application.config["MIN_FREE_MEM_PERC"] = 100

    with pytest.raises(ValueError) as e:
        system_monitor()
        assert "System is over maximum memory threshold." in e

    client_fixture.application.config["MIN_FREE_MEM_PERC"] = old_config
