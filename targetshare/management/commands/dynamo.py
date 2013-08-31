import logging
import sys

from django.core.management.base import CommandError, LabelCommand
from django.db import connection

from targetshare.models import dynamo


class Command(LabelCommand):
    args = '<subcommand0 subcommand1 ...>'
    label = 'subcommand'
    help = "Subcommands: create, migrate, destroy, status"

    def handle_label(self, label, **options):
        logger = logging.getLogger('mysql_to_dynamo')

        if label == 'create':
            dynamo.utils.database.create_all_tables(
                timeout=(60 * 3), # 3 minutes per table
                console=sys.stdout,
            )
            self.stdout.write("Created all Dynamo tables. "
                              "This make take several minutes to take effect.")
        elif label == 'status':
            dynamo.utils.database.status()
        elif label == 'destroy':
            done = dynamo.utils.database.drop_all_tables(confirm=True)
            if done:
                self.stdout.write("Dropped all Dynamo tables. "
                                  "This make take several minutes to take effect.")
        elif label == 'migrate':
            curs = connection.cursor()

            # TOKENS
            logger.debug('Loading tokens')
            curs.execute("""SELECT fbid, appid, token,
                                unix_timestamp(expires) as expires,
                                unix_timestamp(updated) as updated
                            FROM tokens
                            WHERE fbid=ownerid;""")
            names = [d[0] for d in curs.description] # column names

            with dynamo.Token.items.batch_write() as batch:
                for row in curs:
                    batch.put_item(data=dict(zip(names, row)))

            logger.debug('Finished tokens')

            # USERS
            logger.debug('Loading users')
            curs.execute("""SELECT fbid, fname, lname, email, gender,
                                unix_timestamp(birthday) as birthday,
                                city, state,
                                unix_timestamp(updated) as updated
                            FROM users;""")
            names = [d[0] for d in curs.description] # column names

            with dynamo.User.items.batch_write() as batch:
                for row in curs:
                    batch.put_item(data=dict(zip(names, row)))

            logger.debug('Finished users')

            # EDGES
            logger.debug('Loading edges')

            curs.execute("""SELECT fbid_source, fbid_target, post_likes, post_comms,
                                stat_likes, stat_comms, wall_posts, wall_comms,
                                tags, photos_target, photos_other, mut_friends,
                                unix_timestamp(updated) as updated
                            FROM edges;""")
            names = [d[0] for d in curs.description] # column names

            with dynamo.IncomingEdge.items.batch_write() as inc:
                with dynamo.OutgoingEdge.items.batch_write() as out:
                    for row in curs:
                        inc.put_item(data=dict(zip(names, row)))
                        out.put_item(data={'fbid_source': row[0],
                                            'fbid_target': row[1],
                                            'updated': row[-1]})

            logger.debug('Finished edges')
        else:
            raise CommandError("No such subcommand '{}'.".format(label))
