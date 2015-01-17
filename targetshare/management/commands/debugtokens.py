import math
import re
from collections import defaultdict
from functools import partial
from optparse import make_option
from textwrap import dedent

from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from django.core.management.base import NoArgsCommand
from faraday.utils import epoch

from targetshare.integration import facebook
from targetshare.models import dynamo, relational


EPOCH_ZERO = epoch.to_datetime(0)

PHI = 0.5 + 0.5 * math.sqrt(5.0)

_SECRETS = {} # cache


def is_fibonacci(n):
    a = PHI * n
    return n == 0 or abs(round(a) - a) < 1.0 / n


class Counter(object):

    KEYS = ('valid', 'invalid', 'expired')

    def __init__(self, valid=0, invalid=0, expired=0):
        self.valid = valid
        self.invalid = invalid
        self.expired = expired

    def increment(self, attr):
        setattr(self, attr, getattr(self, attr) + 1)

    def __getattr__(self, key):
        match = re.search(r'^increment_(\w+)$', key)
        if match:
            attr = match.group(1)
            if attr in self.KEYS:
                method = partial(self.increment, attr)
                setattr(self, key, method)
                return method

        raise AttributeError("'{}' object has no attribute {!r}"
                             .format(self.__class__.__name__, key))


class CounterRegistry(defaultdict):

    class AppCounterContainer(tuple):

        def __new__(cls, counters=()):
            return super(CounterRegistry.AppCounterContainer, cls).__new__(cls, counters)

        def _do(self, method):
            for counter in self:
                getattr(counter, method)()

        def __getattr__(self, key):
            method = partial(self._do, key)
            setattr(self, key, method)
            return method

    def __init__(self):
        super(CounterRegistry, self).__init__(Counter)

    def get_many(self, keys):
        return self.AppCounterContainer(self[key] for key in keys)


class Command(NoArgsCommand):

    option_list = NoArgsCommand.option_list + (
        make_option('-c', '--client',
                    action='append',
                    dest='client_codenames',
                    metavar='CLIENT',
                    help='Client codenames to which to limit the query'),
    )
    help = dedent("""\
        Debug, update and report on tokens in DynamoDB by querying Facebook

        For example:

            debugtokens

            debugtokens --client=advocates-for-youth --client=wnyc
        """)

    def __init__(self):
        super(Command, self).__init__()
        self.stats = CounterRegistry()

    def echo(self, content):
        self.stdout.write(content, ending='')
        self.stdout.flush()

    def handle_noargs(self, client_codenames, **options):
        # Determine tokens to process #
        if client_codenames:
            client_users = relational.UserClient.objects.filter(client__codename__in=client_codenames)
            user_keys = client_users.values_list('fbid', 'client__fb_app_id').distinct()
            tokens = dynamo.Token.items.batch_get(
                # FIXME: boto requires re-scan & doesn't batch keys
                tuple({'fbid': fbid, 'appid': appid}
                      for (fbid, appid) in user_keys.iterator())
            )
        else:
            tokens = dynamo.Token.items.scan()

        # Process tokens #
        self.echo('Debugging tokens ...')
        (count, update_count, retries) = self.try_many_tokens(tokens.iterable) # FIXME: faraday #9
        self.stdout.write('') # carriage return
        self.stdout.write("Processed {} tokens".format(count))

        # Re-process failed tokens #
        while retries:
            self.echo('Retrying {} tokens ...'.format(len(retries)))
            tokens = dynamo.Token.items.batch_get(retries)
            (count, update_count, retries) = self.try_many_tokens(tokens.iterable, count, update_count) # FIXME: faraday #9
            self.stdout.write('') # carriage return
            self.stdout.write("Processed {} tokens".format(count))

        # Report #
        self.stdout.write("Updated {} tokens".format(update_count))

        if client_codenames:
            self.write_header("Client results")
            self.report((client_codename, self.stats[client_codename]) for client_codename in client_codenames)

            remainder = [client_codename for client_codename in self.stats if client_codename not in client_codenames]
            if remainder:
                self.write_header("Other client results")
                self.report((client_codename, self.stats[client_codename]) for client_codename in remainder)
        else:
            self.report(self.stats.iteritems())

    def write_header(self, content):
        self.stdout.write('')
        self.stdout.write('-' * len(content))
        self.stdout.write(content)
        self.stdout.write('-' * len(content))
        self.stdout.write('')

    def report(self, client_counters):
        # Print header
        self.echo("{0: <40} | ".format('Client'))
        self.stdout.write(' | '.join(key.title() for key in Counter.KEYS))
        self.echo("{} | ".format('-' * 40))
        self.stdout.write(" | ".join('-' * len(key) for key in Counter.KEYS))

        for (client_codename, counter) in client_counters:
            self.echo("{0: <40} | ".format(client_codename))
            values = (str(getattr(counter, key)).ljust(len(key)) for key in counter.KEYS)
            self.stdout.write(" | ".join(values))

    def try_many_tokens(self, tokens, count=0, update_count=0):
        retries = []

        for token in tokens:
            try:
                updated = self.try_token(token)
            except (ConditionalCheckFailedException, KeyError, IOError, RuntimeError):
                retries.append(token.get_keys())
            else:
                count += 1
                update_count += int(updated)
                if count in (55, 610) or count > 1000 and is_fibonacci(count):
                    self.echo(' {} ...'.format(count))

        return (count, update_count, retries)

    def try_token(self, token):
        user_clients = relational.UserClient.objects.filter(fbid=token.fbid, client__fb_app_id=token.appid)
        client_codenames = user_clients.values_list('client__codename', flat=True)
        app_stats = self.stats.get_many(client_codenames.iterator())

        # We expect values of "expires" to be optimistic, meaning we trust dates
        # in the past, but must confirm dates in the future.
        # (We sometimes set field optimistically; and, user can invalidate our
        # token, throwing its actual expires to 0.)

        if not token.expires or token.expires == EPOCH_ZERO:
            app_stats.increment_invalid()
            return False

        if token.expires <= epoch.utcnow():
            app_stats.increment_expired()
            return False

        try:
            secret = _SECRETS[token.appid]
        except KeyError:
            secret = relational.FBApp.objects.values_list('secret', flat=True).get(appid=token.appid)
            _SECRETS[token.appid] = secret

        # Confirm token expiration (and validity)
        debug_result = facebook.client.debug_token(token.appid, secret, token.token)
        debug_data = debug_result['data']
        token_valid = debug_data['is_valid']
        token_expires = debug_data['expires_at']

        # Update token, if needed; but, restart if another process has changed
        # the token (meaning it may now refer to new value):
        token.expires = token_expires
        updated = token.partial_save()

        if token_valid and token.expires > epoch.utcnow():
            app_stats.increment_valid()
        elif token.expires > EPOCH_ZERO:
            app_stats.increment_expired()
        else:
            app_stats.increment_invalid()

        return updated
