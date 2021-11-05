"""Host system monitors."""

import psutil
from flask import current_app as app


def system_monitor() -> None:
    """Group of functions to monitor host OS."""
    # Check if free disk space is below threshold set in config.py.
    my_disk = psutil.disk_usage("/")

    if my_disk.free < app.config["MIN_DISK_SPACE"]:
        raise ValueError("System is below minimum disk space threshold.")

    # Check if cpu is below threshold set in config.py.
    my_cpu = psutil.cpu_percent(interval=5)  # seconds to check cpu

    if my_cpu > 100 - app.config["MIN_FREE_CPU_PERC"]:
        raise ValueError("System is over maximum cpu threshold.")

    # Check if memory is below threshold set in config.py.
    my_mem = psutil.virtual_memory()

    if my_mem.percent > 100 - app.config["MIN_FREE_MEM_PERC"]:
        raise ValueError("System is over maximum memory threshold.")
