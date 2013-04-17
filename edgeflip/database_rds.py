#!/usr/bin/python
import sys
import MySQLdb as mysql

from . import config as conf
config = conf.getConfig(includeDefaults=True)
# import logging

TABLE_PRIMARY_KEYS = {
    'tokens': ['fbid', 'appid', 'ownerid']
}

TABLE_COLS = {
                'users' : """    fbid BIGINT PRIMARY KEY,
                                fname VARCHAR(128),
                                lname VARCHAR(128),
                                gender VARCHAR(8),
                                birthday VARCHAR(16),
                                city VARCHAR(32),
                                state VARCHAR(32),
                                token VARCHAR(512),
                                friend_token VARCHAR(512),
                                updated BIGINT """,

                'tokens' : """  fbid BIGINT,
                                appid BIGINT,
                                ownerid BIGINT,
                                token VARCHAR(512),
                                expires TIMESTAMP,
                                updated TIMESTAMP """,

                'edges' : """    prim_id BIGINT,
                                sec_id BIGINT,
                                in_post_likes INTEGER,
                                in_post_comms INTEGER,
                                in_stat_likes INTEGER,
                                in_stat_comms INTEGER,
                                out_post_likes INTEGER,
                                out_post_comms INTEGER,
                                out_stat_likes INTEGER,
                                out_stat_comms INTEGER,
                                mut_friends INTEGER,
                                updated BIGINT,
                                PRIMARY KEY (prim_id, sec_id) """,

                'events' : """    session_id VARCHAR(128),
                                ip VARCHAR(32),
                                fbid BIGINT,
                                friend_fbid    BIGINT,
                                type VARCHAR(64),
                                appid BIGINT,
                                content VARCHAR(128),
                                activity_id BIGINT,
                                create_dt DATETIME,
                                KEY(session_id),
                                KEY(fbid),
                                KEY(friend_fbid),
                                KEY(activity_id) """
             }



def getConn():
    return mysql.connect(config['dbhost'], config['dbuser'], config['dbpass'], config['dbname'], charset="utf8", use_unicode=True)


# Reset the DB by dropping and recreating tables
def dbSetup(connP=None, tableKeys=None):

    conn = connP if (connP is not None) else getConn()
    curs = conn.cursor()

    if (tableKeys is None):
        tableKeys = TABLE_COLS.keys()
    for t in tableKeys:
        c = TABLE_COLS[t]
        curs.execute("DROP TABLE IF EXISTS %s" % t)
        curs.execute("CREATE TABLE %s ( %s )" % (t, c) )

    conn.commit()
    if (connP is None):
        conn.close()


# Helper class to update records in a table. 
def insert_update(curs, updateTable, coalesceCols, overwriteCols, keyCols, vals):

    allCols = keyCols + overwriteCols + coalesceCols
    keySQL = ' AND '.join([ c + ' = %('+c+')s' for c in keyCols ])

    selectSQL = "SELECT %s FROM %s WHERE %s" % ( ', '.join(keyCols), updateTable, keySQL )

    coalesceSQL  = [ '%s = COALESCE(%s, %s)' % (c, '%('+c+')s', c) for c in coalesceCols ]
    overwriteSQL = [ '%s = %s' % (c, '%('+c+')s') for c in overwriteCols ]
    upColsSQL = ', '.join(overwriteSQL + coalesceSQL)
    updateSQL = "UPDATE %s SET %s WHERE %s" % (updateTable, upColsSQL, keySQL)

    insertSQL = "INSERT INTO %s (%s) VALUES (%s)" % (
                    updateTable, ', '.join(allCols), ', '.join(['%('+c+')s' for c in allCols]) )

    insertCount = 0
    for row in vals:

        curs.execute(selectSQL, row)

        sql = updateSQL if ( curs.fetchone() ) else insertSQL
        curs.execute(sql, row)

        curs.execute("COMMIT")
        insertCount += 1

    return insertCount


