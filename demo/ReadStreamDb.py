import sys
import sqlite3
import datetime




DB_PATH = 'demo.sqlite'




def getConn():
	return sqlite3.connect(DB_PATH)

def dbSetup(conn=None):
	if (conn is None):
		conn = getConn()
	curs = conn.cursor()
	curs.execute("""DROP TABLE IF EXISTS streamcounts""") 
	curs.execute("""CREATE TABLE streamcounts (prim_id INTEGER,
												sec_id INTEGER,
												post_likes INTEGER,
												post_comms INTEGER,
												stat_likes INTEGER,
												stat_comms INTEGER,
												mut_friends INTEGER,
												updated INTEGER,
												PRIMARY KEY (prim_id, sec_id))""")
	conn.commit()

