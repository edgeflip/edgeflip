import base64

from Crypto.Cipher import DES
from django.conf import settings


MESSAGE_PADDING = ' '
BLOCK_SIZE = 8


def pad(s):
    return s + MESSAGE_PADDING * (BLOCK_SIZE - len(s) % BLOCK_SIZE)


ENCODE_PADDING = '='
ENCODE_SIZE = 4


def repad(enc):
    return enc + ENCODE_PADDING * (-len(enc) % ENCODE_SIZE)


# DES appears to be limited to 8-character secret, so truncate if too long
SECRET = pad(settings.CRYPTO.des_secret)[:8]
CIPHER = DES.new(SECRET)


def encodeDES(message):
    """Encrypt a message with DES cipher, returning a URL-safe string.

    The Base-64 padding character `=` is stripped, to avoid quoting issues.
    Companion function `decodeDES` will properly restore this padding on behalf
    of the base64 library, (via `repad`).

    """
    encrypted = CIPHER.encrypt(pad(str(message)))
    b64encoded = base64.urlsafe_b64encode(encrypted)
    return b64encoded.rstrip(ENCODE_PADDING)


def decodeDES(encoded):
    """Decrypt a message with DES cipher."""
    b64decoded = base64.urlsafe_b64decode(repad(str(encoded)))
    return CIPHER.decrypt(b64decoded).rstrip(MESSAGE_PADDING)
