import logging
import random
import base64
import urllib
from Crypto.Cipher import DES

from targetshare.settings import config

logger = logging.getLogger(__name__)


PADDING = ' '
BLOCK_SIZE = 8

pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

# DES appears to be limited to 8-character secret, so truncate if too long
secret = pad(config.crypto.des_secret)[:8]
cipher = DES.new(secret)


class CDFProbsError(Exception):
    """CDF defined by provided experimental probabilities is not well-defined"""
    pass


def rand_assign(tupes):
    """takes a set of tuples of (id, cdf probability) and chooses one id randomly"""

    tupes = sorted(tupes, key=lambda t: t[1])   # ensure sorted by CDF Probability
    check_cdf(tupes)

    rand = random.random()

    # Pick out smallest probability greater than (or equal to) random number
    for obj_id, prob in tupes:
        if prob >= rand:
            return obj_id

    raise CDFProbsError("Math must be broken if we got here...")


def check_cdf(tupes):
    """Takes tuples of (id, CDF Probability) and ensures the CDF is well-defined"""

    probs = sorted([t[1] for t in tupes])
    if (min(probs) <= 0):
        raise CDFProbsError("Zero or negative probabilities detected")
    if (max(probs) != 1.0):
        raise CDFProbsError("Max probability is not 1.0")
    if (len(probs) != len(set(probs))):
        raise CDFProbsError("Duplicate values found in CDF")


def encodeDES(message):
    """Encrypt a message with DES cipher, returning a URL-safe, quoted string"""
    message = str(message)
    encrypted = cipher.encrypt(pad(message))
    b64encoded = base64.urlsafe_b64encode(encrypted)
    encoded = urllib.quote(b64encoded)
    return encoded


def decodeDES(encoded):
    """Decrypt a message with DES cipher, assuming a URL-safe, quoted string"""
    encoded = str(encoded)
    unquoted = urllib.unquote(encoded)
    b64decoded = base64.urlsafe_b64decode(unquoted)
    message = cipher.decrypt(b64decoded).rstrip(PADDING)
    return message
