import time
import threading
import logging
import random
import base64
import urllib
from Crypto.Cipher import DES

import us
import requests
from civis_matcher import matcher
from django.conf import settings
from unidecode import unidecode


logger = logging.getLogger(__name__)


PADDING = ' '
BLOCK_SIZE = 8

pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

# DES appears to be limited to 8-character secret, so truncate if too long
secret = pad(settings.CRYPTO.des_secret)[:8]
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
    probs = sorted(t[1] for t in tupes)
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


def civis_filter(edge, feature, operator, value, matches):
    ''' Performs a match against the Civis API and retrieves the score for a
    given user
    '''
    start_time = time.time()
    user = edge.secondary
    logger.debug('Thread %s started' % threading.current_thread().name)
    cm = matcher.CivisMatcher()
    kwargs = {}
    if user.birthday:
        kwargs['birth_month'] = '%02d' % user.birthday.month
        kwargs['birth_year'] = user.birthday.year
        kwargs['birth_day'] = '%02d' % user.birthday.day

    if not user.state or not user.city:
        return

    if user.state:
        state = us.states.lookup(user.state)
        kwargs['state'] = state.abbr if state else None
    else:
        kwargs['state'] = None

    try:
        start_time = time.time()
        result = cm.match(
            first_name=unidecode(user.fname),
            last_name=unidecode(user.lname),
            city=unidecode(user.city) if user.city else None,
            **kwargs
        )
        end_time = time.time()
        logger.debug(
            'Request time: %s, url: %s',
            (end_time - start_time),
            result.url
        )
    except requests.RequestException:
        return None
    except matcher.MatchException as exc:
        # This means there was an issue with the Civis API. Likely means no
        # match, but it's hard to say in the current state of their API.
        logger.info('Exception: %s' % exc.message)
        return None

    scores = getattr(result, 'scores', None)
    if scores and float(scores[feature][operator]) >= float(value):
        matches.append(edge)
    logger.debug(
        'Thread %s ended: %s' % (
            threading.current_thread().name, time.time() - start_time
        )
    )
    return


class TooFewFriendsError(Exception):
    """Too few friends found in picking best choice set filter"""
    pass
