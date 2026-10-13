"""job_sync clears stale timing fields on disabled tasks."""

from datetime import datetime, timezone

from scheduler.extensions import db
from scheduler.maintenance import job_sync
from scheduler.model import Task

from .conftest import create_demo_task


def test_job_sync_clears_disabled_task_timing(client_fixture: object) -> None:
    """Disabled tasks lose next_run and est_duration; enabled tasks keep them."""
    assert client_fixture is not None
    _project_id, disabled_id = create_demo_task(db.session)
    _project_id, enabled_id = create_demo_task(db.session)
    when = datetime(2030, 6, 1, 12, 0, tzinfo=timezone.utc).replace(tzinfo=None)

    disabled = db.session.get(Task, disabled_id)
    enabled = db.session.get(Task, enabled_id)
    assert disabled is not None
    assert enabled is not None
    disabled.enabled = 0
    disabled.next_run = when
    disabled.est_duration = 30
    enabled.enabled = 1
    enabled.next_run = when
    enabled.est_duration = 45
    db.session.commit()

    job_sync()

    db.session.expire_all()
    disabled = db.session.get(Task, disabled_id)
    enabled = db.session.get(Task, enabled_id)
    assert disabled is not None
    assert enabled is not None
    assert disabled.next_run is None
    assert disabled.est_duration is None
    assert enabled.next_run is not None
    assert enabled.est_duration == 45
