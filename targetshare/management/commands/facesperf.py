import time
from itertools import chain
from optparse import make_option
from Queue import Queue
from threading import Thread

import requests
from django.core.urlresolvers import reverse
from django.core.management.base import CommandError, BaseCommand
from faraday.utils import epoch

from targetshare.models import dynamo, relational


class Command(BaseCommand):

    args = '<server>'
    option_list = BaseCommand.option_list + (
        make_option('--campaign', dest='campaign_id', help='Campaign to query'),
        make_option('--content', dest='client_content_id', help='Client content to query'),
        make_option('--fbidfile', help='Path to file containing fbids to query'),
        make_option('--limit', default=100, type=int, help='Number of queries to make (if fbids not specified)'),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.uri = self.campaign = self.client_content = self.queue = self.verbosity = None
        self.results = []

    def pout(self, msg, verbosity=0):
        if self.verbosity >= verbosity:
            self.stdout.write(msg)

    def perr(self, msg, verbosity=0):
        if self.verbosity >= verbosity:
            self.stderr.write(msg)

    def handle(self, server, campaign_id, client_content_id, fbidfile, limit, **options):
        self.uri = server + reverse('faces')
        if not self.uri.startswith('http'):
            self.uri = 'https://' + self.uri

        self.verbosity = int(options['verbosity'])

        if fbidfile and limit:
            raise CommandError("options --fbidfile and --limit are mutually exclusive")

        self.campaign = relational.Campaign.objects.get(pk=campaign_id)
        self.client_content = relational.ClientContent.objects.get(pk=client_content_id)
        client = self.campaign.client
        fb_app_id = client.fb_app_id
        if client != self.client_content.client:
            raise CommandError("Mismatched campaign and client content")

        if fbidfile:
            # Grab fbids separated by any space (newline, space, tab):
            fbids = chain.from_iterable(line.split() for line in open(fbidfile).xreadlines())
            keys = tuple({'fbid': int(fbid), 'appid': fb_app_id} for fbid in fbids)
            tokens = dynamo.Token.items.batch_get(keys)
        else:
            tokens = dynamo.Token.items.scan(appid__eq=fb_app_id, expires__gt=epoch.utcnow(), limit=limit)

        # Do one thread per primary for now:
        self.queue = Queue()
        for (count, token) in enumerate(tokens, 1):
            thread = Thread(target=self.worker)
            thread.setDaemon(True)
            thread.start()
            self.queue.put((token.fbid, token.token))

        self.queue.join()
        if len(self.results) < count:
            self.perr("Completed polling of {} / {} tokens"
                      .format(len(self.results), count), 1)

        for result in self.results:
            self.stdout.write("{:.1f}".format(result), ending=' ')
        self.stdout.flush()

    def worker(self):
        while True:
            (fbid, token) = self.queue.get()
            try:
                completed_in = self.poll_faces(fbid, token)
            except requests.exceptions.HTTPError:
                self.perr("Error ({})".format(fbid), 1)
            else:
                self.results.append(completed_in)
            self.queue.task_done()

    def poll_faces(self, fbid, token):
        self.pout("Starting ({})".format(fbid), 2)
        t0 = time.time()
        query = {
            'fbid': fbid,
            'token': token,
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
            if (time.time() - t0) > 30:
                query['last_call'] = '1'
            response = session.post(self.uri, query)
            response.raise_for_status()
            message = response.json()

        self.pout("Completed ({})".format(fbid), 2)
        return time.time() - t0
