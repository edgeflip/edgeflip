#!/usr/bin/python
import sys
import time
import logging
import datetime
import threading
import datastructs
import facebook
import database_sqlite as db # modify this to swtch db implementations
from config import config


def getConn():
	return db.getConn()

def dateFromIso(dateStr):
	if (dateStr):
		dateElts = dateStr.split('-')
		if (len(dateElts) == 3): 
			y, m, d = dateElts
			return datetime.date(int(y), int(m), int(d))
	return None		

def getUserDb(connP, userId, freshness=36525, freshnessIncludeEdge=False): # 100 years!
	conn = connP if (connP is not None) else db.getConn()

	freshness_date = datetime.date.today() - datetime.timedelta(days=freshness)
	sql = """SELECT fbid, fname, lname, gender, birthday, city, state, token, friend_token, updated FROM users WHERE fbid=%s""" % userId
	#logging.debug(sql)
	curs = conn.cursor()
	curs.execute(sql)
	rec = curs.fetchone()
	if (rec is None):
		ret = None
	else:
		#logging.debug(str(rec))
		fbid, fname, lname, gender, birthday, city, state, token, friend_token, updated = rec
		if (datetime.date.fromtimestamp(updated) < freshness_date):
			ret = None
		else:
			if (freshnessIncludeEdge):
				curs.execute("SELECT max(updated) as freshnessEdge FROM edges WHERE prim_id=%d" % userId)
				rec = curs.fetchone()
				#logging.debug("got rec: %s" % str(rec))
				updatedEdge = rec[0]
				if (updatedEdge is None) or (datetime.date.fromtimestamp(updatedEdge) < freshness_date):
					ret = None
				else:
					ret = datastructs.UserInfo(fbid, fname, lname, gender, dateFromIso(birthday), city, state)
			else:
				ret = datastructs.UserInfo(fbid, fname, lname, gender, dateFromIso(birthday), city, state)
			#zzz todo: clean this up
	if (connP is None):
		conn.close()
	return ret

def getFriendEdgesDb(connP, primId, requireOutgoing=False, newerThan=0):
	conn = connP if (connP is not None) else db.getConn()
	curs = conn.cursor()
	sql = """
			SELECT prim_id, sec_id,
					in_post_likes, in_post_comms, in_stat_likes, in_stat_comms,
					out_post_likes, out_post_comms, out_stat_likes, out_stat_comms, 
					mut_friends, updated
			FROM edges
			WHERE prim_id=? AND updated>?
	""" 
	if (requireOutgoing):
		sql += """
			AND out_post_likes IS NOT NULL 
			AND out_post_comms IS NOT NULL 
			AND out_stat_likes IS NOT NULL
			AND out_stat_comms IS NOT NULL
		"""
	curs.execute(sql, (primId, newerThan))
	eds = []
	primary = getUserDb(conn, primId)
	for pId, sId, inPstLk, inPstCm, inStLk, inStCm, outPstLk, outPstCm, outStLk, outStCm, muts, updated in curs:
		secondary = getUserDb(conn, sId)
		eds.append(datastructs.Edge(primary, secondary, inPstLk, inPstCm, inStLk, inStCm, outPstLk, outPstCm, outStLk, outStCm, muts))
	if (connP is None):
		conn.close()
	return eds

# helper function that may get run in a background thread
def _updateFriendEdgesDb(user, token, edges):
	tim = datastructs.Timer()
	conn = db.getConn()
	curs = conn.cursor()
	updateUserDb(curs, user, token, None)
	insertCount = 0
	for i, e in enumerate(edges):
		updateUserDb(curs, e.secondary, None, token)
		updateFriendEdgeDb(curs, e)
		insertCount += 1	
	conn.commit()
	logging.debug("updateFriendEdgesDb() thread %d updated %d friends for user %d (took %s)" % (threading.current_thread().ident, insertCount, user.id, tim.elapsedPr()))
	conn.close()
	return insertCount

def updateFriendEdgesDb(user, token, edges, background=False):
	if (background):
		t = threading.Thread(target=_updateFriendEdgesDb, args=(user, token, edges))
		t.daemon = False
		t.start()
		logging.debug("updateFriendEdgesDb() spawning background thread %d for user %d" % (t.ident, user.id))
		return 0
	else:
		logging.debug("updateFriendEdgesDb() foreground thread %d for user %d" % (threading.current_thread().ident, user.id))
		return _updateFriendEdgesDb(user, token, edges)

def updateFriendEdgeDb(curs, edge): # n.b.: doesn't commit
	sql = """
		INSERT OR REPLACE INTO edges VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	"""
	params = (edge.primary.id, edge.secondary.id, 
			edge.inPostLikes, edge.inPostComms, edge.inStatLikes, edge.inStatComms,
			edge.outPostLikes, edge.outPostComms, edge.outStatLikes, edge.outStatComms,
			edge.mutuals, time.time())
	curs.execute(sql, params)

def updateUserDb(curs, user, tok, tokFriend):
	# can leave tok or tokFriend blank, in that case it will not overwrite
	sql = "INSERT OR REPLACE INTO users (fbid, fname, lname, gender, birthday, city, state, token, friend_token, updated) "
	if (tok is None):
		sql += "VALUES (?, ?, ?, ?, ?, ?, ?, (SELECT token FROM users WHERE fbid=?), ?, ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), user.city, user.state, user.id, tokFriend, time.time())
	elif (tokFriend is None):
		sql += "VALUES (?, ?, ?, ?, ?, ?, ?, ?, (SELECT friend_token FROM users WHERE fbid=?), ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), user.city, user.state, tok, user.id, time.time())
	else:
		sql += "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), user.city, user.state, tok, tokFriend, time.time())
	curs.execute(sql, params)

