import logging
import re
from datetime import timedelta
from optparse import make_option
from textwrap import dedent

from django.core.management.base import NoArgsCommand, CommandError
from django.db import connections
from django.db.models.loading import get_model
from django.utils import timezone

from targetshare.models.dynamo import Token


LOG = logging.getLogger('crow')


def get_interval(number, unit):
    """Construct a datetime.timedelta from the given integer value and unit.

    `unit` must be one of 'd', 'h', 'm' or 's'.

    """
    if unit == 'd':
        number *= 24 * 60 * 60
    elif unit == 'h':
        number *= 60 * 60
    elif unit == 'm':
        number *= 60
    elif unit != 's':
        raise ValueError("Invalid unit: {!r}".format(unit))

    return timedelta(seconds=number)


def get_db_now(database):
    """Query the given database for its `NOW()`."""
    connection = connections[database]
    cursor = connection.cursor()
    cursor.execute("SELECT NOW()")
    (now,) = cursor.fetchone()
    return now


class Command(NoArgsCommand):

    option_list = NoArgsCommand.option_list + (
        make_option('-d', '--database', help='Client database connection name'),
        make_option('-m', '--model', dest='model_name', help='Token model name'),
        make_option('-a', '--appid', help='Facebook application ID'),
        make_option(
            '--since',
            help="Limit import to rows updated since timestamp YYYY-MM-DD[ HH:MM:[SS...]] "
                 "or over past given interval of days, hours, minutes or seconds (e.g. 60d)"
        ),
    )
    help = dedent("""\
        Import tokens from a client database

        For example:

            synctokens --database=ofa --model=OFAToken --appid=2349590 --since="2013-07-15 01:01"
        """)

    def handle_noargs(self, database, model_name, appid, since=None, **options):
        if not all([database, model_name, appid]):
            raise CommandError("database, model and appid required.")

        model = get_model('targetclient', model_name)
        tokens = model.objects.using(database).filter(deleted_at=None).order_by('facebook_id')
        if since:
            interval_match = re.search(r'^(\d+)([dhms])$', since)
            if interval_match:
                (number, unit) = interval_match.groups()
                delta = get_interval(int(number), unit)
                now = get_db_now(database)
                since = now - delta

            tokens = tokens.filter(updated_at__gt=since)

        # OFA doesn't record expiration
        expires = timezone.now() + timedelta(days=60)

        count = 0
        try:
            with Token.items.batch_write() as batch:
                for (count, token) in enumerate(tokens.iterator(), 1):
                    batch.put_item(
                        fbid=token.facebook_id,
                        token=token.facebook_access_token,
                        appid=appid,
                        expires=expires,
                    )
        except Exception as exc:
            LOG.exception("synctokens batch write failure")
            self.stderr.write("Batch write failure: {}".format(exc))

        self.stdout.write("Wrote {} tokens from {} to DDB".format(count, database))
