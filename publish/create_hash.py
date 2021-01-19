"""Extract Management 2.0 Publish Script."""
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
import hashlib
import time


def create_hash():
    """Create a hash of the current time.

    :returns: string of hash
    """
    publish_hash = hashlib.sha256()
    publish_hash.update(str(time.time()).encode("utf-8"))
    return str(publish_hash.hexdigest()[:10])


if __name__ == "__main__":
    print(create_hash())  # noqa: T001
