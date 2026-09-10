"""Run with .venv/bin/python -m unittest test_ssh_key_generation."""

import ast
import unittest
from io import StringIO
from pathlib import Path

from flask import Blueprint, Flask, current_app, request
from flask_login import LoginManager, UserMixin, login_required
from flask_wtf.csrf import CSRFProtect, generate_csrf
from paramiko import RSAKey


class SshKeyGenerationTest(unittest.TestCase):
    """Check the key-generation HTTP boundary and generated key material."""

    def test_authenticated_csrf_protected_key_generation(self):
        """Require login and CSRF, and return a usable matching key pair."""
        # Load the actual route without starting Hub's database and Redis services.
        source = ast.parse(Path("web/web/connection.py").read_text())
        route = next(
            node
            for node in source.body
            if isinstance(node, ast.FunctionDef) and node.name == "generate_ssh_key"
        )
        blueprint = Blueprint("connection_bp", __name__)
        namespace = {
            "connection_bp": blueprint,
            "login_required": login_required,
            "RSAKey": RSAKey,
            "StringIO": StringIO,
            "request": request,
            "app": current_app,
            "Response": object,
        }
        exec(  # noqa: S102 -- executes only the repository's route under test
            compile(ast.Module(body=[route], type_ignores=[]), "connection.py", "exec"), namespace
        )
        app = Flask(__name__)
        app.config.update(SECRET_KEY="test-only", TESTING=True)
        manager = LoginManager(app)
        user = UserMixin()
        user.id = "1"
        manager.user_loader(lambda user_id: user)
        app.register_blueprint(blueprint)
        CSRFProtect(app)
        app.add_url_rule("/csrf", view_func=generate_csrf)
        client = app.test_client()
        token = client.get("/csrf").get_data(as_text=True)
        self.assertEqual(
            client.post("/connection/ssh-key", data={"csrf_token": token}).status_code, 401
        )
        with client.session_transaction() as session:
            session["_user_id"] = "1"
            session["_fresh"] = True
        for password in ("", "test-passphrase"):
            response = client.post(
                "/connection/ssh-key", data={"key_password": password, "csrf_token": token}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            key = RSAKey.from_private_key(
                StringIO(response.json["private_key"]), password=password or None
            )
            self.assertEqual(key.get_bits(), 3072)
            self.assertEqual(response.json["public_key"], f"ssh-rsa {key.get_base64()}")
        self.assertEqual(client.post("/connection/ssh-key").status_code, 400)


if __name__ == "__main__":
    unittest.main()
