import logging
import sys
from optparse import make_option

from django.core.management.base import CommandError, LabelCommand

from targetshare.models.dynamo import db, utils
from targetshare import database_compat as database


class Command(LabelCommand):
    args = '<subcommand0 subcommand1 ...>'
    label = 'subcommand'
    help = "Subcommands: create, migrate, destroy"
    option_list = LabelCommand.option_list + (
        make_option(
            '-r', '--read-throughput',
            dest='read_throughput',
            default=5,
            type='int',
            help='Sets the read throughput when creating tables. Default 5.'
        ),
        make_option(
            '-w', '--write-throughput',
            dest='write_throughput',
            default=5,
            type='int',
            help='Sets the write throughput when creating tables. Default 5.'
        ),
    )

    def handle_label(self, label, **options):
        logger = logging.getLogger('mysql_to_dynamo')

        if label == 'create':
            throughput = {
                'read': options.get('read_throughput') or 5,
                'write': options.get('write_throughput') or 5,
            }
            utils.database.create_all_tables(
                timeout=(60 * 3), # 3 minutes per table
                console=sys.stdout,
                throughput=throughput,
            )
            self.stdout.write("Created all Dynamo tables. "
                              "This make take several minutes to take effect.")
        elif label == 'destroy':
            done = utils.database.drop_all_tables(confirm=True)
            if done:
                self.stdout.write("Dropped all Dynamo tables. "
                                  "This make take several minutes to take effect.")
        elif label == 'migrate':
            conn = database.getConn()
            curs = conn.cursor()

            # TOKENS
            logger.debug('Loading tokens')
            table = db.get_table('tokens')
            curs.execute("""SELECT ownerid, appid, token,
                                unix_timestamp(expires),
                                unix_timestamp(updated)
                            FROM tokens
                            WHERE fbid=ownerid;""")
            names = [d[0] for d in curs.description] # column names

            with table.batch_write() as batch:
                for row in curs:
                    batch.put_item(data=dict(zip(names, row)))

            logger.debug('Finished tokens')

            # USERS
            logger.debug('Loading users')
            table = db.get_table('users')
            curs.execute("""SELECT fbid, fname, lname email, gender, birthday, city, state,
                                unix_timestamp(updated)
                            FROM users;""")
            names = [d[0] for d in curs.description] # column names

            with table.batch_write() as batch:
                for row in curs:
                    batch.put_item(data=dict(zip(names, row)))

            logger.debug('Finished users')

            # EDGES
            logger.debug('Loading edges')
            incoming = db.get_table('edges_incoming')
            outgoing = db.get_table('edges_outgoing')

            curs.execute("""SELECT fbid_source, fbid_target, post_likes, post_comms,
                                stat_likes, stat_comms, wall_posts, wall_comms,
                                tags, photos_target, photos_other, mut_friends,
                                unix_timestamp(updated)
                            FROM edges;""")
            names = [d[0] for d in curs.description] # column names

            with incoming.batch_write() as inc, outgoing.batch_write() as out:
                for row in curs:
                    inc.put_item(data=dict(zip(names, row)))
                    out.put_item(data={'fbid_source': row[0],
                                        'fbid_target': row[1],
                                        'updated': row[-1]})

            logger.debug('Finished edges')

            conn.close()
        else:
            raise CommandError("No such subcommand '{}'.".format(label))
