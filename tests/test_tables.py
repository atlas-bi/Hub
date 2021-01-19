# flake8: noqa,
# pylint: skip-file
import pytest


def test_table_project_mine(em_web_authed):
    assert em_web_authed.get("/table/project/mine").status_code == 200


def test_table_project_all(em_web_authed):
    assert em_web_authed.get("/table/project/all").status_code == 200


def test_table_tasklog_userevents(em_web_authed):
    assert em_web_authed.get("/table/tasklog/userevents").status_code == 200


def test_table_user_auth(em_web_authed):
    assert em_web_authed.get("/table/user/auth").status_code == 200


def test_table_connection_tasks(em_web_authed):
    assert em_web_authed.get("/table/connection/1/tasks").status_code == 200


def test_table_job_orphans(em_web_authed):
    assert em_web_authed.get("/table/jobs/orphans").status_code == 200


def test_table_tasks_active(em_web_authed):
    assert em_web_authed.get("/table/tasks/active").status_code == 200


def test_table_tasks_errored(em_web_authed):
    assert em_web_authed.get("/table/tasks/errored").status_code == 200


def test_table_tasks_scheduled(em_web_authed):
    assert em_web_authed.get("/table/tasks/scheduled").status_code == 200


def test_table_task_mine_list(em_web_authed):
    assert em_web_authed.get("/table/tasks/mine/list").status_code == 200


def test_table_task_all_list(em_web_authed):
    assert em_web_authed.get("/table/tasks/all/list").status_code == 200


def test_table_project_tasks(em_web_authed):
    assert em_web_authed.get("/table/project/1/task").status_code == 200


def test_table_project_tasklog(em_web_authed):
    assert em_web_authed.get("/table/project/1/tasklog").status_code == 200


def test_table_task_log(em_web_authed):
    assert em_web_authed.get("/table/task/1/log").status_code == 200


def test_table_all_tasks_log(em_web_authed):
    assert em_web_authed.get("/table/tasks/log").status_code == 200


def test_table_tasks_error_log(em_web_authed):
    assert em_web_authed.get("/table/tasks/errorLog").status_code == 200
