# flake8: noqa,
# pylint: skip-file


def test_cli_create_db(em_web_cli_app):
    from em_web.cli import create_db

    runner = em_web_cli_app.test_cli_runner()
    assert runner.invoke(create_db)


def test_cli_seed(em_web_cli_app):
    from em_web.cli import db_seed

    runner = em_web_cli_app.test_cli_runner()
    assert runner.invoke(db_seed)


def test_cli_seed_demo(em_web_cli_app):
    from em_web.cli import db_seed_demo

    runner = em_web_cli_app.test_cli_runner()
    assert runner.invoke(db_seed_demo)
