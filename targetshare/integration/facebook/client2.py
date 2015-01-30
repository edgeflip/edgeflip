import requests
import logging

from core.utils.version import make_version

from targetshare.models import datastructs, dynamo

from .utils import decode_date, OAuthException


API_VERSION = make_version('2.2')

GRAPH_ENDPOINT = 'https://graph.facebook.com/v{}/'.format(API_VERSION)

LOG = logging.getLogger(__name__)


def get_graph(token, *path, **fields):
    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(fields, access_token=token)

    try:
        response = requests.get(request_path, params=request_params)
        response.raise_for_status()
    except (IOError, RuntimeError) as exc:
        response = getattr(exc, 'response', None)
        reason = getattr(response, 'reason', '')
        content = getattr(response, 'content', '')

        LOG.warning("Error opening Graph URL %s%s %s(%r): %r",
                    request_path,
                    request_params,
                    exc.__class__.__name__,
                    reason,
                    content,
                    exc_info=True)

        if content:
            OAuthException.raise_for_response(content)
        raise

    payload = response.json()
    if 'paging' in payload:
        # TODO: handle paging
        return payload['data']
    return payload


def get_user(token):
    data = get_graph(token, 'me')
    return dynamo.User(
        fbid=data['id'],
        fname=data['first_name'],
        lname=data['last_name'],
        email=data.get('email'),
        gender=data.get('gender'),
        birthday=decode_date(data.get('birthday')),
        bio=data.get('bio', '')[:150],
        # city=location.get('city'), # TODO
        # state=location.get('state'),
        # country=location.get('country'),
    )


def get_friend_edges(user, token):
    # TODO: auth'd friends?
    # TODO: paging
    network = datastructs.UserNetwork()
    for data in get_graph(token, 'me', 'taggable_friends'):
        friend = datastructs.TaggableFriend(
            id=data['id'],
            name=data['name'],
            picture=data['picture']['data']['url'],
        )
        network.append(network.Edge(user, friend, None))
    return network
