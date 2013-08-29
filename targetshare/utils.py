import datetime
import time
import logging
import random
import base64
import urllib
from Crypto.Cipher import DES

import us
import requests
from civis_matcher import matcher
from django.conf import settings


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


def civis_filter(edges, feature, operator, score_value):
    ''' Performs a match against the Civis API and retrieves the score for a
    given user
    '''
    people_dict = {'people': {}}
    for edge in edges:
        user = edge.secondary
        user_dict = {}
        if user.birthday:
            user_dict['birth_month'] = '%02d' % user.birthday.month
            user_dict['birth_year'] = str(user.birthday.year)
            user_dict['birth_day'] = '%02d' % user.birthday.day

        if not user.state or not user.city:
            continue

        state = us.states.lookup(user.state)
        user_dict['state'] = state.abbr if state else None
        user_dict['city'] = user.city
        user_dict['first_name'] = user.fname
        user_dict['last_name'] = user.lname
        people_dict['people'][user.id] = user_dict

    try:
        cm = matcher.CivisMatcher()
        results = cm.bulk_match(people_dict)
    except requests.RequestException:
        logger.exception('Failed to contact Civis')
        return []
    except matcher.MatchException:
        logger.exception('Matcher Error!')
        return []

    valid_ids = []
    for key, value in results.items():
        scores = getattr(value, 'scores', None)
        filter_feature = scores.get(feature) if scores and scores.get(feature) else {}
        if scores and float(filter_feature.get(operator, 0)) >= float(score_value):
            valid_ids.append(str(key))

    return [x for x in edges if str(x.secondary.id) in valid_ids]


class TooFewFriendsError(Exception):
    """Too few friends found in picking best choice set filter"""
    pass


class Timer(object):
    """used for inline profiling & debugging


    XXX i can probably die
    """
    def __init__(self):
        self.start = time.time()

    def reset(self):
        self.start = time.time()

    def elapsedSecs(self):
        return time.time() - self.start

    def elapsedPr(self, precision=2):
        delt = datetime.timedelta(seconds=time.time() - self.start)
        hours = delt.days * 24 + delt.seconds / 3600
        hoursStr = str(hours)
        mins = (delt.seconds - hours * 3600) / 60
        minsStr = "%02d" % (mins)
        secs = (delt.seconds - hours * 3600 - mins * 60)
        if (precision):
            secsFloat = secs + delt.microseconds / 1000000.0 # e.g., 2.345678
            secsStr = (("%." + str(precision) + "f") % (secsFloat)).zfill(3 + precision) # two digits, dot, fracs
        else:
            secsStr = "%02d" % (secs)
        if (hours == 0):
            return minsStr + ":" + secsStr
        else:
            return hoursStr + ":" + minsStr + ":" + secsStr

    def stderr(self, txt=""):
        raise NotImplementedError # what is this intended to do? No stderr please!
