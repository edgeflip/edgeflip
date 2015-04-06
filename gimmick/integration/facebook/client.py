"""Facebook API v2 client"""
import collections
import enum
import logging
import sys
from concurrent import futures

import requests
import requests_futures.sessions
from django.conf import settings

from core.utils.version import make_version

from targetshare import utils
from targetshare import classifier

from mock import patch


LOG = logging.getLogger(__name__)

API_VERSION = make_version('2.3')

GRAPH_ENDPOINT = 'https://graph.facebook.com/v{}/'.format(API_VERSION)

NUM_POSTS = settings.FACEBOOK.stream.get('num_posts_per_endpoint', 100)
CHUNK_SIZE = settings.FACEBOOK.stream.get('chunk_size', 20)
MAX_WAIT = settings.FACEBOOK.stream.get('max_wait', 15)

MAX_RETRIES = 3
THREAD_COUNT = 6

DATA = '''\
Environment,acid mine drainage,0.9,0
Environment,acid rain,0.5,0
Environment,agricultural runoff,0.9,0
Environment,air pollution,0.9,0
Environment,air quality,0.5,0
Environment,algal bloom,0.9,0
Environment,alkali soil,0.9,0
Environment,alternative energy,0.7,0
Environment,anti environment(al)?,0.5,0
Environment,atmosphere,0.2,0
Environment,atmospheric carbon,0.7,0
Environment,atmospheric conditions,0,1
Environment,bioaccumulation,0.9,0
Environment,biobutanol,0.3,0
Environment,biocapacity,0.9,0
Environment,biodegradable,0.5,0
Environment,biodiversity,0.7,0
Environment,bioenergy,0.5,0
Environment,biofuel?s,0.5,0
Environment,biogeography,0.9,0
Environment,biological integrity,0.9,0
Environment,biomagnification,0.9,0
Environment,biome,0.9,0
Environment,biosecurity,0.9,0
Environment,biosphere,0.5,0
Environment,bioterrorism,0,1
Environment,blast fishing,0.4,0
Environment,bottom trawling,0.6,0
Environment,built environment,0,1
Environment,carbon cycle,0.6,0
Environment,carbon diet,0.9,0
Environment,carbon dioxide,0.3,0
Environment,carbon economy,0.9,0
Environment,carbon footprint?s,0.7,0
Environment,carbon pollution,0.8,0
Environment,carbon pricing,0.9,0
Environment,carbon sequestration,0.9,0
Environment,carbon sink,0.9,0
Environment,carbon tax(es)?,0.5,0
Environment,carrying capacity,0.9,0
Environment,CFC,0.4,0
Environment,chlorofluorocarbons,0.4,0
Environment,clean air act,0.8,0
Environment,clean energy,0.6,0
Environment,clean water,0.7,0
Environment,clearcutting,0.5,0
Environment,climate,0.1,0
Environment,climate change,0.9,0
Environment,climate commitment,0.9,0
Environment,climate denier?s,0.9,0
Environment,climate ethics,0.9,0
Environment,climate justice,0.9,0
Environment,climate refugee?s,0.9,0
Environment,climate shock,0.9,0
Environment,CO2,0.4,0
Environment,coal depletion,0.3,0
Environment,coal industry,0.1,0
Environment,conservation,0.1,0
Environment,consumables,0.2,0
Environment,coral bleaching,0.9,0
Environment,corporate sustainability,0.5,0
Environment,crude oil,0.2,0
Environment,DDT,0.3,0
Environment,debt for nature,0.9,0
Environment,deforestation,0.7,0
Environment,desertification,0.8,0
Environment,dirty air,0.4,0
Environment,dirty coal,0.6,0
Environment,dirty energy,0.6,0
Environment,dirty fuel?s,0.7,0
Environment,drawbridge mentality,0.3,0
Environment,earth charter,0.9,0
Environment,Earth Day,0.6,0
Environment,eco terrorism,,1
Environment,eco terrorist?s,,1
Environment,eco efficiency,0.6,0
Environment,eco imperialism,,1
Environment,ecoforestry,0.9,0
Environment,ecological,0.6,0
Environment,ecology,0.3,0
Environment,ecoregion?s,0.9,0
Environment,ecosharing,0.9,0
Environment,ecosystem?s,0.3,0
Environment,ecotax(es)?,0.9,0
Environment,ecotechnology,0.9,0
Environment,ecovillage?s,0.9,0
Environment,ecozone?s,0.9,0
Environment,electric car?s,0.2,0
Environment,electric vehicle?s,0.2,0
Environment,emissions,0.2,0
Environment,emissions trading,0.2,0
Environment,endangered species,0.7,0
Environment,energy conservation,0.6,0
Environment,energy crop?s,0.4,0
Environment,energy economics,0.5,0
Environment,energy efficiency,0.5,0
Environment,environment,0.1,0
Environment,environmental,0.5,0
Environment,environmental extremism,,1
Environment,environmental extremist?s,,1
Environment,environmental protection agency,0.1,0
Environment,environmental terrorism,,1
Environment,environmental terrorist?s,,1
Environment,EPA,0.1,0
Environment,ethical consumerism,0.9,0
Environment,eutrophication,0.9,0
Environment,extinct,0.1,0
Environment,extinction,0.2,0
Environment,extinction event?s,0.4,0
Environment,extreme weather,0.3,0
Environment,flagship species,0.6,0
Environment,food security,0.5,0
Environment,fossil fuel?s,0.2,0
Environment,fracking,0.7,0
Environment,gaia,0.4,0
Environment,gaia theory,0.4,0
Environment,gap analysis,0.5,0
Environment,genetic diversity,0.4,0
Environment,genetic pollution,0.6,0
Environment,genetically modified food?s,0.3,0
Environment,global climate model?s,0.9,0
Environment,global dimming,0.4,0
Environment,global warming,0.5,0
Environment,great pacific garbage patch,0.9,0
Environment,green development,0.7,0
Environment,green energy,0.7,0
Environment,green infrastructure,0.8,0
Environment,green revolution,0.9,0
Environment,greenhouse effect,0.5,0
Environment,greenhouse gas(es)?,0.6,0
Environment,greenhouse mafia,,1
Environment,groundwater contamination,0.9,0
Environment,groundwater pollution,0.9,0
Environment,habitat destruction,0.9,0
Environment,habitat fragmentation,0.9,0
Environment,habitat loss,0.7,0
Environment,holocene extinction,0.3,0
Environment,hostile work environment,0,1
Environment,hybrid car?s,0.2,0
Environment,hybrid vehicle?s,0.2,0
Environment,hydraulic fracturing,0.7,0
Environment,hydrocarbons,0.5,0
Environment,hydrology,0.3,0
Environment,invasive species,0.4,0
Environment,job?s killer?s,,1
Environment,job killing,,1
Environment,keeling curve,0.7,0
Environment,keystone,0.1,0
Environment,kyoto protocol,0.7,0
Environment,land degradation,0.5,0
Environment,land reclamation,0.5,0
Environment,loss of habitat,0.4,0
Environment,low emissions vehicle?s,0.3,0
Environment,low carbon,0.5,0
Environment,marine pollution,0.5,0
Environment,methane,0.3,0
Environment,micro sustainability,0.7,0
Environment,minimal impact code,0.8,0
Environment,mountaintop removal,0.5,0
Environment,national park?s,0.1,0
Environment,natural disaster?s,0.1,0
Environment,nature deficit disorder,0.6,0
Environment,nature preserve?s,0.3,0
Environment,nature reserve?s,0.3,0
Environment,net metering,0.2,0
Environment,new urbanism,0.2,0
Environment,nonpoint source pollution,0.7,0
Environment,ocean acidification,0.8,0
Environment,ocean dumping,0.5,0
Environment,ocean planet,0.6,0
Environment,offshore wind farm,0.4,0
Environment,oil spill?s,0.2,0
Environment,old growth forest?s,0.3,0
Environment,over consumption,0.1,0
Environment,overallocation,0.1,0
Environment,overdrafting,0.1,0
Environment,overfishing,0.5,0
Environment,overgrazing,0.5,0
Environment,overpopulation,0.5,0
Environment,ozone layer,0.2,0
Environment,paleoclimatology,0.5,0
Environment,peak coal,0.2,0
Environment,peak copper,0.1,0
Environment,peak gas,0.2,0
Environment,peak oil,0.3,0
Environment,permaculture,0.3,0
Environment,persistent organic pollutant?s,0.5,0
Environment,pesticide?s,0.3,0
Environment,photovoltaic,0.1,0
Environment,point source pollution,0.4,0
Environment,polar city,0.5,0
Environment,pollinator decline,0.5,0
Environment,polluter pays,0.6,0
Environment,pollution,0.2,0
Environment,power plant?s,0.1,0
Environment,pro business,,1
Environment,pseudo science,,1
Environment,rainforest?s,0.2,0
Environment,rare species,0.3,0
Environment,recycle,0.1,0
Environment,recycling,0.2,0
Environment,regulatory capture,0.2,0
Environment,removal unit?s,0.5,0
Environment,renewable energy,0.8,0
Environment,renewable energies,0.8,0
Environment,renewable resource?s,0.8,0
Environment,renewables,0.7,0
Environment,restoration ecology,0.9,0
Environment,rising sea level?s,0.5,0
Environment,sea levels rise,0.5,0
Environment,slash and burn,0.5,0
Environment,smog,0.3,0
Environment,snowball earth,0.5,0
Environment,soil conservation,0.5,0
Environment,soil contamination,0.2,0
Environment,soil erosion,0.3,0
Environment,soil health,0.3,0
Environment,soil salination,0.6,0
Environment,solar energy,0.7,0
Environment,solar panel?s,0.4,0
Environment,solar power,0.7,0
Environment,spaceship earth,0.8,0
Environment,species extinction,0.6,0
Environment,stewardship,0.2,0
Environment,stop the keystone,0.9,0
Environment,superfund,0.2,0
Environment,sustainability,0.6,0
Environment,sustainable,0.2,0
Environment,sustainable agriculture,0.5,0
Environment,sustainable development,0.2,0
Environment,sustainable energy,0.5,0
Environment,sustainable food,0.3,0
Environment,tar sands,0.2,0
Environment,terraforming,0.2,0
Environment,threatened species,0.5,0
Environment,threshold host density,0.5,0
Environment,toxic chemicals,0.3,0
Environment,toxic waste,0.3,0
Environment,tragedy of the commons,0.7,0
Environment,tree hugger?s,,1
Environment,tropospheric ozone,0.4,0
Environment,urban heat island,0.5,0
Environment,urban runoff,0.6,0
Environment,urban sprawl,0.2,0
Environment,volatile organic compound?s,0.6,0
Environment,vulnerable species,0.6,0
Environment,water conflict,0.5,0
Environment,water conservation,0.6,0
Environment,water scarcity,0.6,0
Environment,water wars,0.6,0
Environment,waterway restoration,0.6,0
Environment,wave farming,0.6,0
Environment,whaling,0.4,0
Environment,wilderness area?s,0.3,0
Environment,wildlife corridor?s,0.5,0
Environment,wildlife reserve?s,0.4,0
Environment,wildlife trade,0.3,0
Environment,wind farm?s,0.6,0
Environment,woodland management,0.4,0
Environment,World Water Day,0.6,0
Environment,zero emissions vehicle?s,0.4,0
'''
CHUNK_SIZE = 15
CHUNKED_DATA = [DATA[pos:(pos + CHUNK_SIZE)] for pos in xrange(0, len(DATA), CHUNK_SIZE)]


def s3_key_xreadlines():
    # Re-chunk by line:
    line = ''
    for chunk in CHUNKED_DATA:
        for byte in chunk:
            line += byte
            if byte == '\n':
                yield line
                line = ''

    # Yield any remainder (for files that do not end with newline):
    if line:
        yield line


@enum.unique
class Permissions(str, enum.Enum):

    PUBLIC_PROFILE = 'public_profile'
    USER_FRIENDS = 'user_friends'
    EMAIL = 'email'
    USER_BIRTHDAY = 'user_birthday'
    USER_LOCATION = 'user_location'
    USER_POSTS = 'user_posts'
    USER_LIKES = 'user_likes'


def _handle_graph_response(response, callback=None, session=None,
                           raise_for_status=False, follow_pagination=True, alert_next=True):
    if raise_for_status:
        response.raise_for_status()

    payload = response.json()
    keys = tuple(payload)
    if 'paging' in keys or keys == ('data',):
        data = payload['data']
        next_ = payload.get('paging', {}).get('next')
        if next_:
            if follow_pagination:
                data.extend(_get_graph(next_))
            elif alert_next:
                LOG.info("Will not traverse pagination: %r", next_)
    else:
        data = payload

    if callback is None:
        return data

    return callback(data, response, session)


def _handle_graph_exception(exc):
    response = getattr(exc, 'response', None)
    request = getattr(response, 'request', None)
    reason = getattr(response, 'reason', '')
    content = getattr(response, 'content', '')
    url = getattr(request, 'url', '')

    if isinstance(exc, (IOError, RuntimeError)):
        LOG.warning("Error opening Graph URL [%s] %s(%r): %s",
                    url,
                    exc.__class__.__name__,
                    reason,
                    content,
                    exc_info=True)
    else:
        LOG.exception("Error in request: %s", exc)

    if hasattr(sys, 'exc_value'):
        # If we're already in the middle of exception-handling,
        # raise exception of appropriate type:
        if content:
            utils.OAuthException.raise_for_response(content)
        raise


def _request_graph(method, path, params=None, data=None):
    try:
        response = requests.request(method, path, data=data, params=params)
        response.raise_for_status()
    except (IOError, RuntimeError) as exc:
        _handle_graph_exception(exc)

    return response


def _get_graph(path, params=None):
    return _handle_graph_response(_request_graph('get', path, params))


def get_graph(token, *path, **fields):
    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(fields, access_token=token, format='json')
    return _get_graph(request_path, request_params)


def get_graph_future(session, token, *path, **kws):
    callback = kws.pop('callback', None)

    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(kws, access_token=token, format='json')

    def background_callback(session, response):
        _handle_graph_response(response, callback, session,
                               raise_for_status=True, follow_pagination=False, alert_next=False)

    return session.get(request_path,
                       params=request_params,
                       background_callback=background_callback)


def post_graph(token, *path, **kws):
    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(kws.get('params', ()), access_token=token, format='json')
    request_data = kws.get('data')
    response = _request_graph('post', request_path, params=request_params, data=request_data)
    return response.json()


def post_notification(app_token, fbid, href, template, ref=None):
    request_params = {'href': href, 'template': template}
    if ref is not None:
        request_params['ref'] = ref
    payload = post_graph(app_token, fbid, 'notifications', params=request_params)
    return payload['success']


Post = collections.namedtuple('Post', ('post_id', 'message'))
Page = collections.namedtuple('Page', ('page_id', 'name'))

class Stream(list):

    @classmethod
    def read(cls, user, token, permissions=Permissions):
        """Construct a new Stream for the given User from the Facebook Graph API."""
        stream = cls(user)

        # Populate Stream.Posts in separate worker threads
        with futures.ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            futures_iter = stream._generate_populators(executor, token, permissions)

            try:
                for done_future in futures.as_completed(tuple(futures_iter), MAX_WAIT):
                    exc = done_future.exception()
                    if exc:
                        # In development, put `done_future.result()` here
                        # to raise exception in main thread.
                        _handle_graph_exception(exc)
            except futures.TimeoutError as exc:
                LOG.warning(
                    "Could not retrieve Facebook data in time (%ss)", MAX_WAIT,
                    exc_info=True
                )

        return stream


    def _generate_populators(self, executor, token, permissions):
        session = requests_futures.sessions.FuturesSession(executor=executor)
        session.mount(GRAPH_ENDPOINT, requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))

        for offset in xrange(0, NUM_POSTS, CHUNK_SIZE):
            if self.permission in permissions:
                yield get_graph_future(session, token, 'me', self.endpoint,
                                       offset=offset,
                                       limit=CHUNK_SIZE,
                                       callback=self._callback(token))

    def __iadd__(self, other):
        if self.user != other.user:
            raise ValueError("Streams belong to different users")
        self.extend(other)
        return self

    def __add__(self, other):
        new = type(self)(self.user, self)
        new += other
        return new

    def __repr__(self):
        data = list(self[:self.REPR_OUTPUT_SIZE + 1])
        if len(data) > self.REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return "{}({!r}, {!r})".format(self.__class__.__name__,
                                       self.user,
                                       data)
    def score(self):
        return 0.2


MAYBE_ENVIRONMENTAL_CATEGORIES = set([
    'Non-profit organization',
])

class LikeStream(Stream):
    permission = Permissions.USER_LIKES
    endpoint = 'likes'


    environmental_subcategories = set([
        'Environmental Conservation'
    ])

    @staticmethod
    def xread(data):
        """Iteratively construct stream from a structured Facebook API response."""
        for datum in data:
            if datum.get('category', '') in MAYBE_ENVIRONMENTAL_CATEGORIES:
                page = Page(
                    page_id=datum['id'],
                    name=datum.get('name', ''),
                )
                yield page


    def __init__(self, user, iterable=()):
        super(LikeStream, self).__init__(iterable)
        self.user = user

    def _callback(self, token):
        def callback(data, response, session):
            pages = self.xread(data)
            for page in pages:
                data = get_graph(token, page.page_id, fields="category_list")
                if any(cat['name'] in self.environmental_subcategories for cat in data.get('category_list', [])):
                    self.append(page)

        return callback

    def score(self):
        score = 0
        for page in self:
           score += 0.02
        return score

class PostStream(Stream):
    permission = Permissions.USER_POSTS
    endpoint = 'feed'

    REPR_OUTPUT_SIZE = 5

    @staticmethod
    def xread(data):
        """Iteratively construct Stream.Posts from a structured Facebook API response."""
        for datum in data:
            post = Post(
                post_id=datum['id'],
                message=datum.get('message', ''),
            )

            yield post

    def __init__(self, user, iterable=()):
        super(PostStream, self).__init__(iterable)
        self.user = user


    def _callback(self, token):
        def callback(data, response, session):
            posts = self.xread(data)
            self.extend(posts)

        return callback

    def score(self):
        weights = classifier.SimpleWeights.load(s3_key_xreadlines())
        qd_post_topics = [
            weights.classify(
                post.message,
                'Environment'
            )
            for post in self
            if post.message
        ]
        print qd_post_topics
        score = sum(item['Environment'] for item in qd_post_topics)
        return score
