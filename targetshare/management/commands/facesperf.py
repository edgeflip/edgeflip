import sys
import time
from itertools import chain
from optparse import make_option
from Queue import Queue
from threading import Thread

import requests
from django.core.urlresolvers import reverse
from django.core.management.base import CommandError, BaseCommand
from faraday.utils import epoch

from targetshare.integration import facebook
from targetshare.models import dynamo, relational


class Command(BaseCommand):

    args = '<server>'
    help = 'Poll the faces endpoint for multiple users with concurrent requests'
    option_list = BaseCommand.option_list + (
        make_option('--campaign', dest='campaign_id', help='Campaign to query'),
        make_option('--content', dest='client_content_id', help='Client content to query'),
        make_option('--fbidfile', help='Path to file containing fbids to query (use - for stdin)'),
        make_option('--limit', type=int, help='Number of concurrent users (if fbids not specified)'),
        make_option('--timeout', type=int, default=30, help='Number of seconds to wait for a response'),
        make_option('--debug', action='store_true', help='Skip tokens that fail a Facebook debugging test'),
        make_option('--random', action='store_true', help='Select tokens randomly'),
    )

    def __init__(self):
        super(Command, self).__init__()
        self._secrets = self.uri = self.campaign = self.client_content = self.verbosity = self.timeout = None

    def pout(self, msg, verbosity=0):
        if self.verbosity >= verbosity:
            self.stdout.write(msg)

    def perr(self, msg, verbosity=0):
        if self.verbosity >= verbosity:
            self.stderr.write(msg)

    def handle(self, server, campaign_id, client_content_id, fbidfile, limit, debug, **options):
        # Init and validate:
        if fbidfile and (limit or options['random']):
            raise CommandError("option --fbidfile incompatible with options --limit and --random")

        self.campaign = relational.Campaign.objects.get(pk=campaign_id)
        self.client_content = relational.ClientContent.objects.get(pk=client_content_id)
        client = self.campaign.client
        fb_app_id = client.fb_app_id
        if client != self.client_content.client:
            raise CommandError("Mismatched campaign and client content")

        self.uri = server + reverse('targetshare:faces')
        if not self.uri.startswith('http'):
            self.uri = 'https://' + self.uri

        self.timeout = options['timeout']
        self.verbosity = int(options['verbosity'])

        if fbidfile:
            fh = sys.stdin if fbidfile == '-' else open(fbidfile)
            # Grab fbids separated by any space (newline, space, tab):
            fbids = chain.from_iterable(line.split() for line in fh.xreadlines())
            keys = tuple({'fbid': int(fbid), 'appid': fb_app_id} for fbid in fbids)
            tokens = dynamo.Token.items.batch_get(keys)
            limit = len(keys)
        else:
            if limit is None:
                limit = 100

            if options['random']:
                app_users = relational.UserClient.objects.filter(client__fb_app_id=fb_app_id)
                random_fbids = app_users.values_list('fbid', flat=True).distinct().order_by('?')
                # A lot of these might be no good when debugged, so get 10x
                # TODO: Use scan and filter by expires?
                # It'd be nice if boto allowed you to specify an (infinite)
                # iterator of keys....
                num_fbids = (limit * 10) if debug else limit
                tokens = dynamo.Token.items.batch_get([{'fbid': fbid, 'appid': fb_app_id}
                                                       for fbid in random_fbids[:num_fbids].iterator()])
            else:
                tokens = dynamo.Token.items.filter(appid__eq=fb_app_id, expires__gt=epoch.utcnow())
                if debug:
                    tokens = tokens.scan()
                else:
                    tokens = tokens.scan(limit=limit)

        tokens = tokens.iterable

        if debug:
            self._secrets = dict(relational.FBApp.objects.values_list('appid', 'secret').iterator())
            tokens = self.debug_tokens(tokens, limit)

        # Do one thread per primary for now:
        queue = Queue()
        results = []
        for (count, token) in enumerate(tokens, 1):
            thread = Thread(target=self.do_poll, args=(queue, results))
            thread.setDaemon(True)
            thread.start()
            queue.put(token)

        queue.join()
        if len(results) < count:
            self.perr("Completed polling of {} / {} tokens"
                      .format(len(results), count), 1)

        for (fbid, result_time) in results:
            self.stdout.write("{}: {:.1f}".format(fbid, result_time))

    def debug_tokens(self, tokens, limit):
        debugged = []
        queue = Queue()
        num = 100 if limit > 100 else limit
        for _count in xrange(num):
            thread = Thread(target=self.do_debug, args=(queue, debugged))
            thread.setDaemon(True)
            thread.start()

        while len(debugged) < limit:
            count = 0
            for (count, token) in enumerate(tokens, 1):
                queue.put(token)
                if count == num:
                    break

            queue.join()
            if count == 0:
                break # we're just out of tokens

        for _count in xrange(num):
            queue.put(None) # relieve debugging threads

        return debugged[:limit]

    def do_debug(self, queue, results):
        while True:
            token = queue.get()

            if token is None:
                # Term sentinel; we're done.
                break

            secret = self._secrets[token.appid]
            result = facebook.client.debug_token(token.appid, secret, token.token)
            data = result['data']
            if data['is_valid'] and data['expires_at'] > time.time():
                results.append(token)

            queue.task_done()

    def do_poll(self, queue, results):
        while True:
            token = queue.get()
            try:
                completed_in = self.poll_faces(token)
            except requests.exceptions.HTTPError as exc:
                self.perr("Error ({}): {!r}".format(token.fbid, exc), 1)
            else:
                results.append((token.fbid, completed_in))
            queue.task_done()

    def poll_faces(self, token):
        self.pout("Starting ({})".format(token.fbid), 2)
        t0 = time.time()
        query = {
            'fbid': token.fbid,
            'token': token.token,
            'num_face': 9,
            'content': self.client_content.pk,
            'campaign': self.campaign.pk,
        }
        session = requests.Session()
        response = session.post(self.uri, query)
        response.raise_for_status()
        message = response.json()
        query.update(
            px3_task_id=message['px3_task_id'],
            px4_task_id=message['px4_task_id'],
        )
        while message['status'] == 'waiting':
            time.sleep(0.5)
            if (time.time() - t0) >= self.timeout:
                query['last_call'] = '1'
            response = session.post(self.uri, query)
            response.raise_for_status()
            message = response.json()

        t1 = time.time()
        self.pout("Completed ({})".format(token.fbid), 2)
        return t1 - t0
