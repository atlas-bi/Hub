"""Password encryption and decryption."""

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


from base64 import b64decode, b64encode

from cryptography.fernet import Fernet


def em_encrypt(text, key):
    """Encrypt a string.

    :param str text: string to decrypt.

    :returns: Encrypted string.
    """
    cipher_suite = Fernet(key)
    byte = b64encode(cipher_suite.encrypt(bytes(text, "utf-8")))
    byte = byte.decode("utf-8")

    return byte


def em_decrypt(text, key):
    """Decrypt a string.

    :param str text: string to decrypt.

    :returns: Decrypted string.
    """
    try:
        cipher_suite = Fernet(key)

        return str(cipher_suite.decrypt(b64decode(text)), "utf-8")
    # pylint: disable=broad-except
    except BaseException:
        return text
