#!/usr/bin/python
import sys
import MySQLdb as mysql
from config import config
import logging


TABLE_COLS = {
				'users' : """	fbid BIGINT PRIMARY KEY,
								fname VARCHAR(128),
								lname VARCHAR(128),
								gender VARCHAR(8),
								birthday VARCHAR(16),
								city VARCHAR(32),
								state VARCHAR(32),
								token VARCHAR(512),
								friend_token VARCHAR(512),
								updated BIGINT """,

				'edges' : """	prim_id BIGINT,
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
								PRIMARY KEY (prim_id, sec_id) """
			 }



def getConn():
	return mysql.connect(config['dbhost'], config['dbuser'], config['dbpass'], config['dbname'], charset="utf8", use_unicode=True)


# Reset the DB by dropping and recreating tables
def dbSetup(connP=None):

	conn = connP if (connP is not None) else getConn()
	curs = conn.cursor()

	for t, c in TABLE_COLS.items():
		curs.execute("DROP TABLE IF EXISTS %s" % t)
		curs.execute("CREATE TABLE %s ( %s )" % (t, c) )

	conn.commit()
	if (connP is None):
		conn.close()


# Helper class to update records in a table. 
# NOTE: Doesn't commit.
def insert_update(curs, updateTable, tmpTable, coalesceCols, overwriteCols, joinCols, vals):

	curs.execute("DROP TABLE IF EXISTS %s" % tmpTable)
	curs.execute("CREATE TEMPORARY TABLE %s ( %s )" % (tmpTable, TABLE_COLS[updateTable]))

	insertCount = 0
	tmpInsertSQL = "INSERT INTO "+tmpTable+" VALUES ("+( ', '.join(["%s"]*len(vals[0])) )+")"
	for v in vals:
		logging.debug('Executing: %s' % (tmpInsertSQL % v) )
		curs.execute(tmpInsertSQL, v)
		insertCount += 1

	coalesceSQL  = [ 'u.%s = COALESCE(t.%s, u.%s)' % (c, c, c) for c in coalesceCols ]
	overwriteSQL = [ 'u.%s = t.%s' % (c, c) for c in overwriteCols ]
	upCols = overwriteSQL + coalesceSQL
	upColsSQL = ', '.join(upCols)
	joinSQL = ' AND '.join(['u.%s = t.%s' % (c, c) for c in joinCols])

	updateSQL = """UPDATE %s AS u, %s AS t
						SET %s
						WHERE %s
				 """ % (updateTable, tmpTable, upColsSQL, joinSQL)
	curs.execute(updateSQL)

	insertSQL = """INSERT INTO %s (
					SELECT t.* FROM %s AS t LEFT JOIN %s AS u ON %s
					WHERE u.%s IS NULL )
				 """ % (updateTable, tmpTable, updateTable, joinSQL, joinCols[0])
	curs.execute(insertSQL)

	curs.execute("DROP TABLE IF EXISTS %s" % tmpTable)

	return insertCount


