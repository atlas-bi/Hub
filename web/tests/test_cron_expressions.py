"""Exhaustive boundary tests for project cron expressions."""

# ruff: noqa: D103

import importlib
from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest
from cron_descriptor import ExpressionDescriptor
from cron_validator import CronValidator
from flask import url_for
from sqlalchemy import Integer, String

from web.extensions import db
from web.model import Project

FIELDS = {
    "cron_year": "2030-2040/2",
    "cron_month": "jan-mar,dec",
    "cron_week": "1-53/2",
    "cron_day": "1,15,last",
    "cron_week_day": "mon-fri",
    "cron_hour": "*/6",
    "cron_min": "0,15,30,45",
    "cron_sec": "10-50/10",
}


def validator(**overrides) -> CronValidator:
    values = dict.fromkeys(FIELDS)
    values["cron"] = 1
    values.update(overrides)
    return CronValidator(**values)


@pytest.mark.parametrize(("field", "expression"), FIELDS.items())
def test_validator_accepts_supported_expression_in_every_field(field, expression) -> None:
    validator(**{field: expression}).validate()


@pytest.mark.parametrize(
    ("field", "expression"),
    [
        ("cron_year", "999"),
        ("cron_month", "13"),
        ("cron_week", "54"),
        ("cron_day", "32"),
        ("cron_week_day", "funday"),
        ("cron_hour", "24"),
        ("cron_min", "60"),
        ("cron_sec", "60"),
    ],
)
def test_validator_rejects_out_of_range_expression_in_every_field(field, expression) -> None:
    with pytest.raises(ValueError, match=r"^Invalid cron schedule:"):
        validator(**{field: expression}).validate()


@pytest.mark.parametrize("expression", ["1,,2", "*/0", "1-", "abc/2", "1 2"])
def test_validator_rejects_malformed_expressions(expression) -> None:
    with pytest.raises(ValueError, match=r"^Invalid cron schedule:"):
        validator(cron_min=expression).validate()


def test_disabled_cron_skips_expression_validation() -> None:
    validator(cron=0, cron_min="not cron").validate()


def test_blank_fields_use_apscheduler_defaults() -> None:
    validator(**dict.fromkeys(FIELDS, "")).validate()


@pytest.mark.parametrize(
    ("values", "expected_fragments"),
    [
        ({"cron_hour": "0", "cron_min": "5", "cron_sec": "9"}, ("12:05:09 AM",)),
        ({"cron_day": "1,2,13"}, ("1st", "2nd", "13th")),
        ({"cron_month": "jan,12"}, ("January", "December")),
        ({"cron_week_day": "mon,6"}, ("Monday", "Sunday")),
        (
            {"cron_hour": "*/6", "cron_min": "0,30", "cron_sec": "10-50/10"},
            ("*/6", "0,30", "10-50/10"),
        ),
    ],
)
def test_descriptor_renders_numeric_and_expression_values(values, expected_fragments) -> None:
    description = ExpressionDescriptor(**values).get_full_description()
    assert all(fragment in description for fragment in expected_fragments)


@pytest.mark.parametrize("module_name", ["web.model", "scheduler.model", "runner.model"])
def test_all_runtime_models_store_every_cron_field_as_string(module_name) -> None:
    project = importlib.import_module(module_name).Project
    for field in FIELDS:
        column_type = getattr(project, field).property.columns[0].type
        assert isinstance(column_type, String)
        assert column_type.length == 120


def test_migration_converts_every_cron_field_in_both_directions(monkeypatch) -> None:
    migration = importlib.import_module("migrations.versions.41eb15d37c84_")
    batch = MagicMock()
    monkeypatch.setattr(
        migration.op, "batch_alter_table", lambda *_args, **_kwargs: nullcontext(batch)
    )

    migration.upgrade()
    upgrade_calls = batch.alter_column.call_args_list
    assert [call.args[0] for call in upgrade_calls] == list(FIELDS)
    assert all(isinstance(call.kwargs["type_"], String) for call in upgrade_calls)

    batch.reset_mock()
    migration.downgrade()
    downgrade_calls = batch.alter_column.call_args_list
    assert [call.args[0] for call in downgrade_calls] == list(reversed(FIELDS))
    assert all(isinstance(call.kwargs["type_"], Integer) for call in downgrade_calls)


def cron_form(name: str, **overrides) -> dict[str, str]:
    data = {
        "project_name": name,
        "project_desc": "cron expression regression",
        "project_cron": "1",
        "project_cron_year": "2030-2040/2",
        "project_cron_mnth": "jan-mar,dec",
        "project_cron_week": "1-53/2",
        "project_cron_day": "1,15,last",
        "project_cron_wday": "mon-fri",
        "project_cron_hour": "*/6",
        "project_cron_min": "0,15,30,45",
        "project_cron_sec": "10-50/10",
    }
    data.update(overrides)
    return data


def test_project_create_and_edit_preserve_cron_expressions(client_fixture) -> None:
    created = cron_form("Expression project")
    response = client_fixture.post("/project/new", data=created, follow_redirects=True)
    assert response.status_code == 200
    project = Project.query.filter_by(name="Expression project").one()
    assert [getattr(project, field) for field in FIELDS] == list(FIELDS.values())

    edited = cron_form(
        "Edited expression project",
        project_cron_year="2031",
        project_cron_mnth="apr-jun",
        project_cron_week="2-20/3",
        project_cron_day="2,16,last",
        project_cron_wday="tue-sat",
        project_cron_hour="8-18/2",
        project_cron_min="*/20",
        project_cron_sec="5,25,45",
    )
    response = client_fixture.post(
        url_for("project_bp.edit_project", project_id=project.id),
        data=edited,
        follow_redirects=True,
    )
    assert response.status_code == 200
    db.session.refresh(project)
    expected = [
        "2031",
        "apr-jun",
        "2-20/3",
        "2,16,last",
        "tue-sat",
        "8-18/2",
        "*/20",
        "5,25,45",
    ]
    assert [getattr(project, field) for field in FIELDS] == expected


def test_invalid_cron_expression_does_not_create_project(client_fixture) -> None:
    before = Project.query.count()
    response = client_fixture.post(
        "/project/new",
        data=cron_form("Invalid expression project", project_cron_min="60"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Invalid cron schedule" in response.get_data(as_text=True)
    assert Project.query.count() == before
