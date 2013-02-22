import sys
import sqlite3
import datetime
import json

try:
	ef_config = open('edgeflip.config', 'r')
	ef_dict = json.loads(ef_config.read())
	if (not ef_dict['outdir']):
		ef_dict['outdir'] = ''
except:
	ef_dict = {'outdir' : ''}



DB_PATH = ef_dict['outdir']+'demo.sqlite'




def getConn():
	return sqlite3.connect(DB_PATH)

def dbSetup(conn=None):
	if (conn is None):
		conn = getConn()
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

