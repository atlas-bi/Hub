"""Password encryption and decryption."""


from base64 import b64decode, b64encode

from cryptography.fernet import Fernet


def em_encrypt(text, key):
    """Encrypt a string."""
    cipher_suite = Fernet(key)
    byte = b64encode(cipher_suite.encrypt(bytes(text, "utf-8")))
    byte = byte.decode("utf-8")

    return byte


def em_decrypt(text, key):
    """Decrypt a string."""
    try:
        cipher_suite = Fernet(key)

        return str(cipher_suite.decrypt(b64decode(text)), "utf-8")
    # pylint: disable=broad-except
    except BaseException:
        return text
