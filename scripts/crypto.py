"""Password encryption and decryption."""

from base64 import b64decode, b64encode

from cryptography.fernet import Fernet


def em_encrypt(text: str, key: str) -> str:
    """Encrypt a string."""
    cipher_suite = Fernet(key)
    byte_string = b64encode(cipher_suite.encrypt(bytes(text, "utf-8")))
    byte = byte_string.decode("utf-8")

    return byte


def em_decrypt(text: str, key: str) -> str:
    """Decrypt a string."""
    try:
        cipher_suite = Fernet(key)

        return str(cipher_suite.decrypt(b64decode(text)), "utf-8")
    # pylint: disable=broad-except
    except BaseException:
        return text
