"""
    used for password encrypt/decrypt

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

from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from em import app


def em_decrypt(text):
    """ decrypt string """
    try:
        obj = AES.new(app.config["SECRET_KEY"], AES.MODE_CBC, app.config["IV_KEY"])
        my_string = obj.decrypt(b64decode(text))
        return str((my_string[0 : len(my_string) // 16]), "utf-8")

    # pylint: disable=bare-except
    except:
        return text


def em_encrypt(text):
    """ encript string """
    obj = AES.new(app.config["SECRET_KEY"], AES.MODE_CBC, app.config["IV_KEY"])
    byte = b64encode(obj.encrypt(text * 16))
    byte = byte.decode("utf-8")

    return byte
