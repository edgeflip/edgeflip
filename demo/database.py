#!/usr/bin/python
import sys
import time
import logging
import datetime
import threading
import datastructs
import facebook
import database_rds as db # modify this to swtch db implementations
import config as conf
config = conf.getConfig(includeDefaults=True)


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
	logging.debug("getting user %s, freshness date is %s" % (userId, freshness_date.strftime("%Y-%m-%d %H:%M:%S")))
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
		updateDate = datetime.date.fromtimestamp(updated)
		logging.debug("getting user %s, update date is %s" % (userId, updateDate.strftime("%Y-%m-%d %H:%M:%S")))

		if (updateDate <= freshness_date):
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
			WHERE prim_id=%s AND updated>%s
	""" % (primId, newerThan)
	if (requireOutgoing):
		sql += """
			AND out_post_likes IS NOT NULL 
			AND out_post_comms IS NOT NULL 
			AND out_stat_likes IS NOT NULL
			AND out_stat_comms IS NOT NULL
		"""
	curs.execute(sql)
	eds = []
	primary = getUserDb(conn, primId)
	for pId, sId, inPstLk, inPstCm, inStLk, inStCm, outPstLk, outPstCm, outStLk, outStCm, muts, updated in curs:
		secondary = getUserDb(conn, sId)
		# For now, hard code Nones into Edge constructor until we integrate the new features into the DB
		eds.append(datastructs.EdgeFromCounts(primary, secondary, inPstLk, inPstCm, inStLk, inStCm,
											  None, None, None, outPstLk, outPstCm, outStLk, outStCm, None, None, None, None, None, muts))
	if (connP is None):
		conn.close()
	return eds

# helper function that may get run in a background thread
def _updateDb(user, token, edges):
	tim = datastructs.Timer()
	conn = db.getConn()
	curs = conn.cursor()
	updateUsersDb(curs, [user], token, None) 
	fCount = updateUsersDb(curs, [e.secondary for e in edges], None, token)
	eCount = updateFriendEdgesDb(curs, edges)
	conn.commit()
	logging.debug("updateFriendEdgesDb() thread %d updated %d friends and %d edges for user %d (took %s)" % (threading.current_thread().ident, fCount, eCount, user.id, tim.elapsedPr()))
	conn.close()
	return eCount

def updateDb(user, token, edges, background=False):
	if (background):
		t = threading.Thread(target=_updateDb, args=(user, token, edges))
		t.daemon = False
		t.start()
		logging.debug("updateDb() spawning background thread %d for user %d" % (t.ident, user.id))
		return 0
	else:
		logging.debug("updateDb() foreground thread %d for user %d" % (threading.current_thread().ident, user.id))
		return _updateDb(user, token, edges)


"""	ip VARCHAR(32),
								fbid BIGINT,
								friend_fbid	BIGINT,
								type VARCHAR(64),
								appid BIGINT,
								content VARCHAR(128),
								activity_id BIGINT,
								create_dt DATETIME,
								KEY(fbid),
								KEY(friend_fbid),
								KEY(activity_id) """

# helper function that may get run in a background thread
def _writeEventsDb(ip, userId, friendIds, eventType, appId, content, activityId):
	tim = datastructs.Timer()
	conn = db.getConn()
	curs = conn.cursor()

	rows = [ {	'ip' : ip, 'userId' : userId, 'friendId' : friendId, 
				'eventType' : eventType, 'appId' : appId, 'content' : content,
				'activityId' : activityId, 'createDt' : time.strftime("%Y%m%d %H:%M:%S") 
			 } for friendId in friendIds ]
	sql = """INSERT INTO events (ip, fbid, friend_fbid, type, appid, content, activity_id, create_dt) 
				VALUES (%(ip)s, %(userId)s, %(friendId)s, %(eventType)s, %(appId)s, %(content)s, %(activityId)s, %(createDt)s) """

	insertCount = 0
	for row in rows:
		curs.execute(sql, row)
		conn.commit()
		insertCount += 1

	logging.debug("_writeEventDb() thread %d updated %d %s event(s) from ip %s" % (threading.current_thread().ident, insertCount, eventType, ip) )
	conn.close()
	
	return insertCount

def writeEventsDb(ip, userId, friendIds, eventType, appId, content, activityId, background=False):
	# friendIds should be a list (as we may want to write multiple shares or suppressions at the same time)
	if (background):
		t = threading.Thread(target=_writeEventsDb, args=(ip, userId, friendIds, eventType, appId, content, activityId))
		t.daemon = False
		t.start()
		logging.debug("writeEventsDb() spawning background thread %d for %s event from ip %s" % (t.ident, eventType, ip))
		return 0
	else:
		logging.debug("writeEventsDb() foreground thread %d for %s event from ip %s" % (threading.current_thread().ident, eventType, ip))
		return _writeEventsDb(ip, userId, friendIds, eventType, appId, content, activityId)


# will not overwrite full crawl values with partial crawl nulls unless explicitly told to do so
def updateFriendEdgesDb(curs, edges, overwriteOutgoing=False): 

	incoming = ['in_post_likes', 'in_post_comms', 'in_stat_likes', 'in_stat_comms']
	outgoing = ['out_post_likes', 'out_post_comms', 'out_stat_likes', 'out_stat_comms']

	coalesceCols = []
	overwriteCols = incoming + ['mut_friends', 'updated']
	if (overwriteOutgoing):
		overwriteCols.extend(outgoing)
	else:
		coalesceCols.extend(outgoing)

	joinCols = ['prim_id', 'sec_id']

	vals = [ {
				'prim_id' : e.primary.id, 'sec_id' : e.secondary.id, 
				'in_post_likes' : e.inPostLikes, 'in_post_comms' : e.inPostComms,
				'in_stat_likes' : e.inStatLikes, 'in_stat_comms' : e.inStatComms,
				'out_post_likes' : e.outPostLikes, 'out_post_comms' : e.outPostComms,
				'out_stat_likes' : e.outStatLikes, 'out_stat_comms' : e.outStatComms,
				'mut_friends' : e.mutuals, 'updated' : time.time() 
			 } for e in edges ]

	return db.insert_update(curs, 'edges', coalesceCols, overwriteCols, joinCols, vals)


def updateUsersDb(curs, users, tok, tokFriend):

	coalesceCols = ['token', 'friend_token']
	overwriteCols = ['fname', 'lname', 'gender', 'birthday', 'city', 'state', 'updated']
	joinCols = ['fbid']

	vals = [ { 
				'fbid' : u.id, 'fname' : u.fname, 'lname' : u.lname, 'gender' : u.gender, 
				'birthday' : str(u.birthday), 'city' : u.city, 'state' : u.state, 
			   	'token' : tok, 'friend_token' : tokFriend, 'updated' : time.time()
			 } for u in users ]

	return db.insert_update(curs, 'users', coalesceCols, overwriteCols, joinCols, vals)


