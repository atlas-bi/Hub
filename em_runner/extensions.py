"""
EM Runner Extensions.

Set up basic flask items for import in other modules.

*Items Setup*

:db: database
:executor: task executor

These items can be imported into other
scripts after running :obj:`em_scheduler.create_app`

"""
# Extract Management 2.0
# Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from flask_executor import Executor
from flask_redis import FlaskRedis
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_caching import CachingQuery

db = SQLAlchemy(query_class=CachingQuery)
executor = Executor()
redis_client = FlaskRedis()
