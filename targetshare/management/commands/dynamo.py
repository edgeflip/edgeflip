import logging

from django.core.management.base import CommandError, LabelCommand

from targetshare import database_compat as database, models


class Command(LabelCommand):
    args = '<subcommand0 subcommand1 ...>'
    label = 'subcommand'
    help = "Subcommands: create, migrate, destroy"

    def handle_label(self, label, **options):
        logger = logging.getLogger('mysql_to_dynamo')

        if label == 'create':
            models.dynamo.create_all_tables(
                timeout=(60 * 3), # 3 minutes per table
            )
            self.stdout.write("Created all Dynamo tables. "
                              "This make take several minutes to take effect.")
        elif label == 'destroy':
            done = models.dynamo.drop_all_tables(confirm=True)
            if done:
                self.stdout.write("Dropped all Dynamo tables. "
                                  "This make take several minutes to take effect.")
        elif label == 'migrate':
            conn = database.getConn()
            curs = conn.cursor()

            # TOKENS
            logger.debug('Loading tokens')
            table = models.dynamo.get_table('tokens')
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
            table = models.dynamo.get_table('users')
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
            incoming = models.dynamo.get_table('edges_incoming')
            outgoing = models.dynamo.get_table('edges_outgoing')

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
