# flake8: noqa,
# pylint: skip-file


from datetime import datetime

import pytest
from flask import g

from em_web.model import Project, Task, TaskLog, User


def test_tasks_home(em_web_authed):
    assert em_web_authed.get("/task").status_code == 200


def test_tasks_mine(em_web_authed):
    assert em_web_authed.get("/task/mine", follow_redirects=True).status_code == 200


def tast_tasks_user(em_web_authed):
    assert em_web_authed.get("/task/user/1").status_code == 200


# add a task
def test_create_task(em_web_authed):
    project = Project(
        name="test project",
        description="my project description",
    )

    db = g.get("db")
    db.session.rollback()
    db.session.add(project)
    db.session.commit()

    g.task_project_id = project.id

    task = Task(
        name="test task",
        project_id=project.id,
        status_id=1,
        enabled=1,
    )

    db.session.add(task)
    db.session.commit()

    g.task_task_id = task.id

    # disable the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/disable", follow_redirects=True
        ).status_code
        == 200
    )

    # enable the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/enable", follow_redirects=True
        ).status_code
        == 200
    )

    # reschedule the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/schedule", follow_redirects=True
        ).status_code
        == 200
    )

    # run the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/run", follow_redirects=True
        ).status_code
        == 200
    )

    # duplicate the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/run", follow_redirects=True
        ).status_code
        == 200
    )

    # cancel retry the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/endretry", follow_redirects=True
        ).status_code
        == 200
    )

    # task hello
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/hello", follow_redirects=True
        ).status_code
        == 200
    )

    # tasks for user
    user = User.query.first()
    if user:
        assert (
            em_web_authed.get(
                "/task/user" + str(user.id), follow_redirects=True
            ).status_code
            == 200
        )

    # attempt to enable from project level
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/enable", follow_redirects=True
        ).status_code
        == 200
    )
    # attempt to disable from project level
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/disable", follow_redirects=True
        ).status_code
        == 200
    )

    # attempt to run from the project level
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/run", follow_redirects=True
        ).status_code
        == 200
    )

    # delete the task
    assert (
        em_web_authed.get(
            "/task/" + str(task.id) + "/delete", follow_redirects=True
        ).status_code
        == 200
    )
    assert Task.query.filter(id == g.get("task_task_id")).count() < 1

    # delete the project
    assert (
        em_web_authed.get(
            "/project/" + str(project.id) + "/delete", follow_redirects=True
        ).status_code
        == 200
    )
    assert Project.query.filter(id == g.get("task_project_id")).count() < 1


def test_new_task(em_web_authed):

    project = Project.query.first()

    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = em_web_authed.post(
        "/project/" + str(project.id) + "/task/new",
        data={
            "name": "Test task",
            "enabled": 0,
        },
        headers=headers,
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_task_params(em_web_authed):
    project = Project.query.first()

    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = em_web_authed.post(
        "/project/" + str(project.id) + "/task/new",
        data={
            "name": "Test task params",
            "enabled": 0,
            "sourceType": 1,  # database
            "sourceQueryType": 4,  # source code
            "sourceCode": "Declare @test int = 1;\nDeclare @test_two int = 2;Set @test_colon int = 1;",
            "queryParams": "@test=2\n@test_colon:2\n@test_two=parse(%Y)",
        },
        headers=headers,
        follow_redirects=True,
    )
    # check source code for params
    # task/1923/source
    # need to check the code here
    assert response.status_code == 200


def test_edit_task(em_web_authed):

    task = Task.query.first()

    mimetype = "application/x-www-form-urlencoded"
    headers = {"Content-Type": mimetype, "Accept": mimetype}
    response = em_web_authed.post(
        "/task/" + str(task.id) + "/edit",
        data={
            "name": "Test task",
            "enabled": 0,
        },
        headers=headers,
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_task_git(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/git")


def test_task_source(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/source")


def test_task_url(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/url")


def test_task_processing_git(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/processing_git")


def test_task_processing_source(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/processing_source")


def test_task_processing_url(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/processing_url")


def test_task_run_log(em_web_authed):

    task = TaskLog.query.first()

    response = em_web_authed.get(
        "/task/" + str(task.task_id) + "/runlog/" + str(task.job_id)
    )


def test_sftp_dest(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/sftp-dest")


def test_sftp_dest(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/sftp-dest")


def test_gpg_file(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/gpg-file")


def test_sftp_source(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/sftp-source")


def test_ssh_source(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/ssh-source")


def test_sftp_query(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/sftp-query")


def test_sftp_processing(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/sftp-processing")


def test_ftp_dest(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/ftp-dest")


def test_ftp_source(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/ftp-source")


def test_ftp_processing(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/ftp-processing")


def test_ftp_query(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/ftp-query")


def test_smb_source(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/smb-source")


def test_smb_dest(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/smb-dest")


def test_smb_query(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/smb-query")


def test_smb_processing(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/smb-processing")


def test_database_source(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get("/task/" + str(task.id) + "/database-source")


def test_reset(em_web_authed):

    task = Task.query.first()

    response = em_web_authed.get(
        "/task/" + str(task.id) + "/reset", follow_redirects=True
    )
    assert response.status_code == 200
