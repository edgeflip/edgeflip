#!/usr/bin/python
import sys
import sqlite3
import config as conf
config = conf.getConfig(includeDefaults=True)




def getConn():
	return sqlite3.connect(config['dbpath'])

def dbSetup(connP=None):
	conn = connP if (connP is not None) else getConn()
	curs = conn.cursor()

	curs.execute("""DROP TABLE IF EXISTS edges""") 
	curs.execute("""CREATE TABLE edges (prim_id INTEGER,
											sec_id INTEGER,
											in_post_likes INTEGER,
											in_post_comms INTEGER,
											in_stat_likes INTEGER,
											in_stat_comms INTEGER,
											out_post_likes INTEGER,
											out_post_comms INTEGER,
											out_stat_likes INTEGER,
											out_stat_comms INTEGER,
											mut_friends INTEGER,
											updated REAL,
											PRIMARY KEY (prim_id, sec_id))""")

	curs.execute("""DROP TABLE IF EXISTS users""") 
	curs.execute("""CREATE TABLE users (fbid INTEGER PRIMARY KEY,
											fname TEXT,
											lname TEXT,
											gender TEXT,
											birthday INTEGER,
											city TEXT,
											state TEXT,
											token TEXT,
											friend_token TEXT,
											updated REAL)""")


	conn.commit()
	if (connP is None):
		conn.close()

