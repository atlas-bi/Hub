"""

    Model structure for user authentication logging.
    This model is independent of the rest of the table.

    Extract Management 2.0
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

"""

from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.sql import func
from em import db


@dataclass
class LoginType(db.Model):
    """
    lookup table of user login types
    """

    __tablename__ = "login_type"
    id: int
    name: str

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    login = db.relationship("Login", backref="login_type", lazy=True)


@dataclass
class Login(db.Model):
    """
    table should contain all login attempts
    """

    __tablename__ = "login"
    id: int
    username: str
    login_date: datetime

    id = db.Column(db.Integer, primary_key=True, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey(LoginType.id), nullable=True)
    username = db.Column(db.String(120), nullable=False)
    login_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
