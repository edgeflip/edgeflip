import json
import us
import logging
import requests
from civis_matcher import matcher

from targetshare.models import dynamo

logger = logging.getLogger(__name__)


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
        if state:
            user_dict['state'] = state.abbr
        user_dict['city'] = user.city
        user_dict['first_name'] = user.fname
        user_dict['last_name'] = user.lname
        people_dict['people'][user.fbid] = user_dict

    try:
        cm = matcher.CivisMatcher()
        results = cm.bulk_match(people_dict)
    except requests.RequestException:
        logger.exception('Failed to contact Civis')
        return []
    except matcher.MatchException:
        logger.exception('Matcher Error!')
        return []

    valid_ids = set()
    for key, value in results.items():
        scores = getattr(value, 'scores', None) or {}
        filter_feature = scores.get(feature) or {}
        if scores and float(filter_feature.get(operator, 0)) >= float(score_value):
            valid_ids.add(long(key))

    return [x for x in edges if x.secondary.fbid in valid_ids]


def civis_cached_filter(edges, feature, operator, score_value):
    valid_ids = set()
    for edge in edges:
        try:
            cr = dynamo.CivisResult.items.get_item(fbid=edge.secondary.fbid)
        except dynamo.CivisResult.DoesNotExist:
            logger.info('No civis result for {}'.format(edge.secondary.fbid))
            continue

        data = json.loads(cr['result']).get('result') or {}
        scores = data.get('scores') or {}
        score = scores.get(feature) or {}
        if score and float(score.get(operator, 0)) >= float(score_value):
            valid_ids.add(long(edge.secondary.fbid))

    return [x for x in edges if x.secondary.fbid in valid_ids]
