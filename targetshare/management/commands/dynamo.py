import sys
from optparse import make_option

from django.core.management.base import CommandError, LabelCommand
from django.db import connection

from targetshare.models import dynamo
from targetshare.models.dynamo.base import db


class Command(LabelCommand):
    args = '<subcommand0 subcommand1 ...>'
    label = 'subcommand'
    help = "Subcommands: create, migrate, destroy, status"
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

    def handle_label(self, label, read_throughput, write_throughput, **options):
        if label == 'create':
            db.build(
                timeout=(60 * 3), # 3 minutes per table
                stdout=sys.stdout,
                throughput={
                    'read': read_throughput,
                    'write': write_throughput,
                },
            )
            self.stdout.write("Created all Dynamo tables. "
                              "This make require several minutes to take effect.")

        elif label == 'status':
            for (table_name, status) in db.status():
                self.stdout.write("{}: {}".format(table_name, status))

        elif label == 'destroy':
            if db.destroy(confirm=True):
                self.stdout.write("Dropped all Dynamo tables. "
                                  "This make require several minutes to take effect.")

        elif label == 'migrate':
            curs = connection.cursor()

            # TOKENS
            self.stdout.write('Loading tokens')
            curs.execute("""SELECT fbid, appid, token,
                                unix_timestamp(expires) as expires,
                                unix_timestamp(updated) as updated
                            FROM tokens
                            WHERE fbid=ownerid;""")
            names = [d[0] for d in curs.description] # column names

            with dynamo.Token.items.batch_write() as batch:
                for row in curs:
                    batch.put_item(data=dict(zip(names, row)))

            self.stdout.write('Finished tokens')

            # USERS
            self.stdout.write('Loading users')
            curs.execute("""SELECT fbid, fname, lname, email, gender,
                                unix_timestamp(birthday) as birthday,
                                city, state,
                                unix_timestamp(updated) as updated
                            FROM users;""")
            names = [d[0] for d in curs.description] # column names

            with dynamo.User.items.batch_write() as batch:
                for row in curs:
                    batch.put_item(data=dict(zip(names, row)))

            self.stdout.write('Finished users')

            # EDGES
            self.stdout.write('Loading edges')

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

            self.stdout.write('Finished edges')

        else:
            raise CommandError("No such subcommand '{}'.".format(label))
