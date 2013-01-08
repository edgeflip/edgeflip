#!/usr/bin/python
import sys
import urllib
import urllib2
import json
import time
from joblib import Parallel, delayed
from collections import defaultdict
import logging
logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(message)s',
					filename='demo.log',
					level=logging.DEBUG)




NUM_JOBS = 10
STREAM_NUM_DAYS = 120
STREAM_CHUNK_DAYS = 10

class STREAMTYPE:
	GROUP_CREATED = 11
	EVENT_CREATED = 12
	STATUS_UPDATE = 46
	WALL_POST = 56
	NOTE_CREATED = 66
	LINK = 80
	VIDEO = 128
	PHOTO = 247
	APP_STORY = 237
	COMMENT_CREATED = 257
	APP_STORY2 = 272
	CHECKIN = 285
	GROUP_POST = 308

FQL_STREAM_CHUNK = " ".join("""SELECT created_time, post_id, source_id, target_id, type FROM stream
								WHERE source_id=%s AND %d <= created_time AND created_time < %d LIMIT 5000""".split())
FQL_POST_COMMS = "SELECT fromid FROM comment WHERE post_id IN (SELECT post_id FROM %s WHERE type != " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_POST_LIKES = "SELECT user_id FROM like WHERE post_id IN (SELECT post_id FROM %s WHERE type != " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_STAT_COMMS = "SELECT fromid FROM comment WHERE post_id IN (SELECT post_id FROM %s WHERE type = " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_STAT_LIKES = "SELECT user_id FROM like WHERE post_id IN (SELECT post_id FROM %s WHERE type = " + str(STREAMTYPE.STATUS_UPDATE) + ")"


def getFriends(user, token):
	fql = """SELECT name, uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = %s)""" % (user)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	responseFile = urllib2.urlopen(url, timeout=60)
	responseJson = json.load(responseFile)
	#sys.stderr.write("responseJson: " + str(responseJson) + "\n\n")
	#friendIds = [ rec['uid2'] for rec in responseJson['data'] ]
	friendTups = [ (rec['uid'], rec['name']) for rec in responseJson['data'] ]
	return friendTups


class StreamCounts(object):
	def __init__(self, userId, stream=[], postLikers=[], postCommers=[], statLikers=[], statCommers=[]):
		self.id = userId
		self.stream = []
		self.friendId_postLikeCount = defaultdict(int)
		self.friendId_postCommCount = defaultdict(int)
		self.friendId_statLikeCount = defaultdict(int)
		self.friendId_statCommCount = defaultdict(int)
		#sys.stderr.write("got post likers: %s\n" % (str(postLikers)))
		#sys.stderr.write("got post commers: %s\n" % (str(postCommers)))
		#sys.stderr.write("got stat likers: %s\n" % (str(statLikers)))
		#sys.stderr.write("got stat commers: %s\n" % (str(statCommers)))
		self.stream.extend(stream)
		self.addPostLikers(postLikers)
		self.addPostCommers(postCommers)
		self.addStatLikers(statLikers)
		self.addStatCommers(statCommers)
	def __iadd__(self, other):
		self.stream.extend(other.stream)
		for fId, cnt in other.friendId_postLikeCount.items():
			self.friendId_postLikeCount[fId] += cnt
		for fId, cnt in other.friendId_postCommCount.items():
			self.friendId_postCommCount[fId] += cnt
		for fId, cnt in other.friendId_statLikeCount.items():
			self.friendId_statLikeCount[fId] += cnt
		for fId, cnt in other.friendId_statCommCount.items():
			self.friendId_statCommCount[fId] += cnt
		return self		
	def __add__(self, other):
		if (self.id != other.id):
			raise Exception("cannot add stream counts for different users (%d, %d)" % (self.id, other.id))
		sc = StreamCounts(self.id)
		sc += self
		sc += other
		return sc
	def __str__(self):		
		ret = "%d entries" % (len(self.stream))
		ret += ", %d post likes" % (sum(self.friendId_postLikeCount.values()))
		ret += ", %d post comments" % (sum(self.friendId_postCommCount.values()))
		ret += ", %d stat likes" % (sum(self.friendId_statLikeCount.values()))
		ret += ", %d stat comments" % (sum(self.friendId_statCommCount.values()))
		#ret += "\n"
		#ret += "stream %s\n" % (id(self.stream))
		#for i in range(min(5, len(self.stream))):
			#ret += "\t" + str(self.stream[i]) + "\n"
		return ret			
			
	def addPostLikers(self, friendIds):
		for friendId in friendIds:
			self.friendId_postLikeCount[friendId] += 1
	def addPostCommers(self, friendIds):
		for friendId in friendIds:
			self.friendId_postCommCount[friendId] += 1
	def addStatLikers(self, friendIds):
		for friendId in friendIds:
			self.friendId_statLikeCount[friendId] += 1
	def addStatCommers(self, friendIds):
		for friendId in friendIds:
			self.friendId_statCommCount[friendId] += 1

	def getPostLikes(self, friendId):
		return self.friendId_postLikeCount.get(friendId, 0)
	def getPostComms(self, friendId):
		return self.friendId_postCommCount.get(friendId, 0)
	def getStatLikes(self, friendId):
		return self.friendId_statLikeCount.get(friendId, 0)
	def getStatComms(self, friendId):
		return self.friendId_statCommCount.get(friendId, 0)

	def getFriendIds(self):
		fIds = set()
		fIds.update(self.friendId_postLikeCount.keys())
		fIds.update(self.friendId_postCommCount.keys())
		fIds.update(self.friendId_statLikeCount.keys())
		fIds.update(self.friendId_statCommCount.keys())
		return fIds		
	def getFriendRanking(self):
		fIds = self.getFriendIds()
		friendId_total = defaultdict(int)
		for fId in fIds:
			friendId_total[fId] += self.friendId_postLikeCount.get(fId, 0)*2
			friendId_total[fId] += self.friendId_postCommCount.get(fId, 0)*4
			friendId_total[fId] += self.friendId_statLikeCount.get(fId, 0)*2
			friendId_total[fId] += self.friendId_statCommCount.get(fId, 0)*4
		return sorted(fIds, key=lambda x: friendId_total[x], reverse=True)

class Edge(object):
	def __init__(self, sc1, sc2):
		self.id1 = sc1.id
		self.id2 = sc2.id
		self.inPostLikes = sc1.getPostLikes(sc2.id)
		self.inPostComms = sc1.getPostComms(sc2.id)
		self.inStatLikes = sc1.getStatLikes(sc2.id)
		self.inStatComms = sc1.getStatComms(sc2.id)
		self.outPostLikes = sc2.getPostLikes(sc1.id)
		self.outPostComms = sc2.getPostComms(sc1.id)
		self.outStatLikes = sc2.getStatLikes(sc1.id)
		self.outStatComms = sc2.getStatComms(sc1.id)
	def __str__(self):
		ret = ""
		for c in[self.inPostLikes, self.inPostComms, self.inStatLikes, self.inStatComms, self.outPostLikes, self.outPostComms, self.outStatLikes, self.outStatComms]:
			ret += "%2s " % str(c)
		return ret
		
	def prox(self,
			inPostLikesMax, inPostCommsMax, inStatLikesMax, inStatCommsMax,
			outPostLikesMax, outPostCommsMax, outStatLikesMax, outStatCommsMax):

		px3 = 1.0 * 1.0
		#zzz need photo tags, mutual friends
		
		px4 = 0.0
		px4 += float(self.inPostLikes) / inPostLikesMax * 1.0
		px4 += float(self.inPostComms) / inPostCommsMax * 1.0
		px4 += float(self.inStatLikes) / inStatLikesMax * 2.0
		px4 += float(self.inStatComms) / inStatCommsMax * 1.0
		#zzz need other tags					

		px5 = 0.0
		px5 += float(self.outPostLikes) / outPostLikesMax * 2.0
		px5 += float(self.outPostComms) / outPostCommsMax * 3.0
		px5 += float(self.outStatLikes) / outStatLikesMax * 2.0
		px5 += float(self.outStatComms) / outStatCommsMax * 16.0
		#zzz need other tags					

		norm = 1.0 + 5.0 + 23.0 # must match weights above
		return (px3 + px4 + px5) / norm


def getFriendRanking(userP, tok, maxFriends=sys.maxint):
	user = int(userP)	
	logging.info('reading stream for user %s, %s', user, tok)
	sc = readStreamParallel(user, tok, STREAM_NUM_DAYS, STREAM_CHUNK_DAYS, NUM_JOBS)
	logging.debug('got %s', str(sc))

	friendId_name = dict(getFriends(user, tok))
	logging.debug("got %d friends total", len(friendId_name))

	friendIdsRanked = sc.getFriendRanking()[:maxFriends]
	logging.debug("got %d friends ranked", len(friendIdsRanked))

	friendId_edge = {}
	for i, friendId in enumerate(friendIdsRanked):
		logging.info("reading friend stream %d/%d (%s)", i, len(friendIdsRanked), friendId)
		try:
			scFriend = readStreamParallel(friendId, tok, STREAM_NUM_DAYS, STREAM_CHUNK_DAYS, NUM_JOBS)
		except Exception:
			logging.warning("error reading stream for %d", friendId)
			continue
		logging.debug('got %s', str(scFriend))
		e = Edge(sc, scFriend)
		logging.debug('edge %s', str(e))
		friendId_edge[friendId] = e
	logging.info("have %d edges", len(friendId_edge))
	
	ipl = max(sc.friendId_postLikeCount.values())
	ipc = max(sc.friendId_postCommCount.values())
	isl = max(sc.friendId_statLikeCount.values())
	isc = max(sc.friendId_statCommCount.values())
	opl = max([ e.inPostLikes for e in friendId_edge.values() ])
	opc = max([ e.inPostComms for e in friendId_edge.values() ])
	osl = max([ e.inStatLikes for e in friendId_edge.values() ])
	opc = max([ e.inStatComms for e in friendId_edge.values() ])		
	friendId_score = dict([ [e.id2, e.prox(ipl, ipc, isl, isc, opl, opc, osl, opc)] for e in friendId_edge.values() ])

	friendTups = []
	for friendId, score in sorted(friendId_score.items(), key=lambda x: x[1], reverse=True):
		edge = friendId_edge[friendId]
		name = friendId_name.get(friendId, "???")
		friendTups.append((friendId, name, str(edge), score))
	return friendTups

def readStreamParallel(userId, token, numDays=100, chunkSizeDays=20, jobs=4, timeout=60):
	intervals = [] # (ts1, ts2)
	chunkSizeSecs = chunkSizeDays*24*60*60
	tsNow = int(time.time())
	tsStart = tsNow-numDays*24*60*60
	for ts1 in range(tsStart, tsNow, chunkSizeSecs):
		ts2 = min(ts1 + chunkSizeSecs, tsNow)
		intervals.append((ts1, ts2))
	scChunks = Parallel(n_jobs=jobs)(delayed(readStreamChunk)(userId, token, ts1, ts2) for ts1, ts2 in intervals)
			
	logging.debug("%d chunk results for user %s", len(scChunks), userId)
	sc = StreamCounts(userId)
	for scChunk in scChunks:
		logging.debug("chunk " + str(scChunk))
		sc += scChunk
	return sc
	
def readStreamChunk(userId, token, ts1, ts2, timeout=60):
	queryJsons = []
	streamLabel = "stream"
	queryJsons.append('"%s":"%s"' % (streamLabel, urllib.quote_plus(FQL_STREAM_CHUNK % (userId, ts1, ts2))))
	streamRef = "#" + streamLabel
	queryJsons.append('"postLikes":"%s"' % (urllib.quote_plus(FQL_POST_LIKES % (streamRef))))
	queryJsons.append('"postComms":"%s"' % (urllib.quote_plus(FQL_POST_COMMS % (streamRef))))
	queryJsons.append('"statLikes":"%s"' % (urllib.quote_plus(FQL_STAT_LIKES % (streamRef))))
	queryJsons.append('"statComms":"%s"' % (urllib.quote_plus(FQL_STAT_COMMS % (streamRef))))
	queryJson = '{' + ','.join(queryJsons) + '}'
	#sys.stderr.write(queryJson + "\n\n")

	url = 'https://graph.facebook.com/fql?q=' + queryJson + '&format=json&access_token=' + token	
	#sys.stderr.write(url + "\n\n")

	try:
		responseFile = urllib2.urlopen(url, timeout=60)
	except Exception as e:
		logging.warning("error reading stream chunk for user %s (%s - %s): %s\n" % (userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)), str(e)))
		return StreamCounts(userId)
	responseJson = json.load(responseFile)
	#sys.stderr.write("responseJson: " + str(responseJson)[:1000] + "\n\n")

	lab_recs = {}
	for entry in responseJson['data']:
		label = entry['name']
		records = entry['fql_result_set']
		#sys.stderr.write(label + ": " + str(records) + "\n\n")
		lab_recs[label] = records
	#return lab_recs
	pLikeIds = [ r['user_id'] for r in lab_recs['postLikes'] ]
	pCommIds = [ r['fromid'] for r in lab_recs['postComms'] ]
	sLikeIds = [ r['user_id'] for r in lab_recs['statLikes'] ]
	sCommIds = [ r['fromid'] for r in lab_recs['statComms'] ]
	sc = StreamCounts(userId, lab_recs['stream'], pLikeIds, pCommIds, sLikeIds, sCommIds)
	return sc
	



USER_TUPS = [
		(500876410, 'rayid', 'AAABlUSrYhfIBAFkDiI9l4ZBj7hKyTywQ1WkZCkw5uiWfZAUFKh73glIsEcgS390CQas9Ya8vZAMNMUnqdZCR3EhgX3ImLRF0Xy64zspM0DQZDZD'),
		(1546335889, 'tim', 'AAABlUSrYhfIBAMEo3RepupV7S9VjEjfFYxNZBrMQxutJ6ygidtFHafNwxz4ZA6m5Up4qQNIQkPk35EOAMeBZApZC1oZBKRtAlqREiCHYE1QZDZD'),
		(6963, 'michelangelo', 'AAABlUSrYhfIBAA7QmZBaEotpI4KRtTqgpMXgmG4qr76qAHH4mAzNSyCwjH6kgZCvAo99fg0SZCZAnYBZCq3IAnFaq8GjV1ZCkZD'),
		(1726740242, '---', 'AAABlUSrYhfIBAJZBjFh2ZBbgbY2O70pt0rrV13n6rYn4ZC4B7M5Hxrq6Yp64sOrAnEvjtFxmki59GaBBP7bzHkAsDEgwwtRwSUjFkElWgZDZD'),
		(727085031, '---', 'AAABlUSrYhfIBAJ8mFpQSectZAPUqRoTy38Byl7nojMscxMEi66H4qKASkUNSSI1h8RZB9ubS5SdZCiRch6ZBMOWJUQIeVlYoXdzBdUs7AQZDZD'),
		(100000530413808, '---', 'AAABlUSrYhfIBANj7nxOLFLqmUY4VG1ElRbK88p55lVZCKgYZAwrJKI5kA6rZCyT2e7f78xtuMG63BN4nUmXiwIn5dZBL4wFGj1u4Tg3UewZDZD'),
		(1193661144, '---', 'AAABlUSrYhfIBAEwdWSxjofpM5lRDkG0EC8sKJz1fYzhoDjjZCPUvDiWVywHxW6aL9RucWraGtkc2WmNBrdzdcUS1hKjYZA5iqe0STKowZDZD'),
		(100000226411771, '---', 'AAABlUSrYhfIBAP73x86UbRcKuE4WAmR0IsaCwyNvPMukxhBsKWcuzP8JycYsZChug1lgAXDBjG2rmoualRewXjePt2VqL22yZCIgiiRQZDZD'),
		(1130651020, '---', 'AAABlUSrYhfIBAAP2ZBe5zaWQnhUqxZBdbwjQYcjlLIGdukyjEHZAbg76vRwAP3mD3s44YpefZBv4ZBBQB8wcaqiNpUpqZBpCevqXVngYrILwZDZD'),
		(676731154, '---', 'AAABlUSrYhfIBANWAZA6Sb6h81iPS5vnFLObxnsnlXQOt9ZBx2RqizTWJWUeX56YWTCCmETtT7cT5VtK6T1KM14EFLVZAV8XYoPuRqncnwZDZD'),
		(100004360602886, '---', 'AAABlUSrYhfIBAHgiPdXaPLnuZAkzDo8WtDhZCQxYAyHKUOhoGNGvRZCZAr34rl1qxytTpzFCw0tEZAJ5kP2rbFrhVeI9waWtZBrNHWlhzqowZDZD'),
		(1036154377, '---', 'AAABlUSrYhfIBAOZBSIsGZAe8pm2Wj2VXPpwxOU7T8LZAYGpMjPaFZBNTCdBDEnPfUBOZAE1tzEN6bC2sBiZAaE7muSZA1laQRtrY0OWpYDKSoehhmKhJ6DO'),
		(635379288, '---', 'AAABlUSrYhfIBAFbBjEFI4LKfC0u77zeIY7h8IpopNDiPAGFsJ5ZCskgTEVXiInob6UexzDcVJ5cJ1fUXd7QGtsZAHHiDCdXiRcZCZB5D9gZDZD'),
		(27222909, '---', 'AAABlUSrYhfIBAFseiI3WPjNvJQN9SvraBwex6LkDU8HzXzw3uuWzb4wcFqInhiJVEZCV68ounBefDFuh4m5DKT224IDi2fO064ojGEwZDZD'),
		(1008191, '---', 'AAABlUSrYhfIBAGCdhhyKwiZBZBFMjVDcinCgdZBEsXSPBwsAXuiGbMu5BZACgQP6TyaRrDoxFHLB5EOT00fZCVKjQNLB6heAZD'),
		(543580444, '---', 'AAABlUSrYhfIBAB2z6DMbVu0oQdUuj46rlpPhNXaCzmdU1hZAXUdr8Ox3Gfli1mBJZB7gVX3X5e6wWShDWjWNrJAc0Jp3A3hpZC35ZAl82AZDZD'),
		(840880135, '---', 'AAABlUSrYhfIBAOnHL8ZAsiQvyTww0hEXLdx6pZCww3rj7IwAEbPgqP2KgJQ31uIig9ZB1iV2mVfIp8maARYzW0z46AlHi2iOozo1ltNwwZDZD'),
		(1487430149, '---', 'AAABlUSrYhfIBAE5ZC9GYWatTd22qouQd3NkWg9DBJZAHoV1MDwnkPWOVEOJc0cz2TJihMZBfD9l0ZBNnoBJNcR0K9uJEWeUNb1VJjBZAJ2gZDZD'),
		(100001694456083, '---', 'AAABlUSrYhfIBANwo8ghIOfscJkpWgZARHZCe0qWWZAE2U7PWvf9ZB1Tg0jnZBg7DvUUmZBk9QQZA1mZAmfm9tnHeXZAGpE36XHQ40zHXfN9p55gZDZD'),
		(1509232539, '---', 'AAABlUSrYhfIBAFOpiiSrYlBxIvCgQXMhPPZCUJWM70phLO4gQbssC3APFza3kZCMzlgcMZAkmTjZC9UACIctzDD4pn2ulXkZD'),
		(1623041802, '---', 'AAABlUSrYhfIBABinXNRPLyjW6bSWKbQZAT6X2XyBkov5oo1JWc8pqHZCgR775kLwX6k7KGKxDKwVSRPGh0K80yvqIEEUBDIfsb9C7KpgZDZD'),
		(1176046827, '---', 'AAABlUSrYhfIBADWM3erqRb4p3lGZBwCT6apifRGGuXHz8ZC1DUblK7GxGXDG1qa4QPBiTdVsvg19HqDEnxbNzZCGXqU1LbZCbk3Ed2Hz0AZDZD'),
		(1586985595, '---', 'AAABlUSrYhfIBAJpZBogkxZANKb6BVgIo371SaCrZCRSqtmQXMKtu0GML3mUdbXW1sTiBvWX7fZAyj1XhUG13AxHAd9XmuCuVVMD6Kekt3gZDZD'),
		(100004262284455, '---', 'AAABlUSrYhfIBAAd7OQabTURjCrRcLj7m0FUZBLvP441scgZB5lxIZARApMdZBpkBOzy8lz0grwo99n8QWoRBjaEXmHn8bISdqjbC7OqwsAZDZD'),
		(1320023169, '---', 'AAABlUSrYhfIBAJ2DRmZAlyab8QmpACPYdthZAZCUwyKHEYURZBT4UMDFScAQn2uVuTnjuDVY0e9MVZBZBCWoBpr8Wm8DUYnUaxO1AAN7P3BgZDZD'),
		(100001558181442, '---', 'AAABlUSrYhfIBAMyMCuZCl3J8ZAiAEYmaX9nIxrhR4xXnI6pt70slY59QydSd53Va6oJk9ser19rxbwjIjtJa2AcEpMt6CT8hcO0KRZCNQZDZD'),
		(100000066778288, '---', 'AAABlUSrYhfIBAJXn2nzhSWS9G1BlHZCZCyd7Ymow4Q31m6z10KPIVx7WYBexxIcXY2RtJbxE56V6IJB2Wbu8Rqkpb0TPybiPhWBokYkgN9z8NZBaaRZB'),
		(1556426182, '---', 'AAABlUSrYhfIBAGZCAztEoD04VgnYZAhSdBvlsuU0NObIVoV8vwlipV5XmZAcp92ZCbevNo9ZArSyRaPWBv0ZCSSWoCZCqAgMXXZC02c99Iln6AZDZD')
	]




#####################################################

if (__name__ == '__main__'):
	

	if (len(sys.argv) > 1):
		users = [ int(u) for u in sys.argv[1:] ]
	else:	
		users = [ t[0] for t in USER_TUPS ]

	user_info = dict([ (t[0], (t[1], t[2])) for t in USER_TUPS ])
	for i, user in enumerate(users):
		nam, tok = user_info[user]

		friendTups = getFriendRanking(user, tok) # id, name, desc, score
		for friendId, name, desc, score in friendTups:
			sys.stderr.write("friend %20s %30s %s %.4f\n" % (friendId, name, desc, score))

