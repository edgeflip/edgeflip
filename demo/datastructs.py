#!/usr/bin/python
import sys
import time
import datetime
from unidecode import unidecode




class Timer(object):
	def __init__(self):
		self.start = time.time()
	def reset(self):
		self.start = time.time()
	def elapsedSecs(self):
		return time.time() - self.start
	def elapsedPr(self, precision=2):
		delt = datetime.timedelta(seconds=time.time() - self.start)
		hours = delt.days*24 + delt.seconds/3600
		hoursStr = str(hours)
		mins = (delt.seconds - hours*3600)/60
		minsStr = "%02d" % (mins)
		secs = (delt.seconds - hours*3600 - mins*60)
		if (precision):
			secsFloat = secs + delt.microseconds/1000000.0 # e.g., 2.345678
			secsStr = (("%." + str(precision) + "f") % (secsFloat)).zfill(3 + precision) # two digits, dot, fracs
		else:
			secsStr = "%02d" % (secs)
		if (hours == 0):
			return minsStr + ":" + secsStr
		else:
			return hoursStr + ":" + minsStr + ":" + secsStr
	def stderr(self, txt=""):
		sys.stderr.write(self.elapsedPr() + " " + txt + "\n")

# util func to deal with Nones, numbers, and unisuck
def unidecodeSafe(s):
	if (s is None):
		return "?"
	else:
		try:
			return str(s)
		except UnicodeEncodeError:
			return unidecode(s)

class UserInfo(object):
	def __init__(self, uid, first_name, last_name, sex, birthday, city, state):
		self.id = uid
		self.fname = first_name
		self.lname = last_name
		self.gender = sex
		self.birthday = birthday
		self.age = int((datetime.date.today() - self.birthday).days/365.25) if (birthday) else None
		self.city = city
		self.state = state
	def __str__(self):
		rets = [ str(self.id),
				 unidecodeSafe(self.fname),
				 unidecodeSafe(self.lname),
				 self.gender,
				 unidecodeSafe(self.age),
				 unidecodeSafe(self.city),
				 unidecodeSafe(self.state) ]
		return " ".join(rets)

class FriendInfo(UserInfo):
	def __init__(self, primId, friendId, first_name, last_name, sex, birthday, city, state, primPhotoTags, otherPhotoTags, mutual_friend_count):
		super(FriendInfo, self).__init__(self, friendId, first_name, last_name, sex, birthday, city, state)
		self.idPrimary = primId
		self.primPhotoTags = primPhotoTags
		self.otherPhotoTags = otherPhotoTags
		self.mutuals = mutual_friend_count


class Edge(object):
	def __init__(self, primInfo, secInfo):
		self.primary = primInfo
		self.secondary = secInfo
		self.inPostLikes = None
		self.inPostComms = None
		self.inStatLikes = None
		self.inStatComms = None
		self.inWallPosts = None  # Posts by secondary or primary's wall
		self.inWallComms = None  # Comments by primary on those posts. These might be considered "outgoing" but are found in the primary's stream
		self.inTags = None       # Tags of the secondary in a primary's post on the primary's wall. Again, might be considered "outgoing" but appear in the priamry's stream...
		self.outPostLikes = None
		self.outPostComms = None
		self.outStatLikes = None
		self.outStatComms = None
		self.outWallPosts = None    # Posts by primary on secondary's wall
		self.outWallComms = None    # Comments by secondary on those posts
		self.outTags = None         # Tags of primary in a secondary's post on their wall
		self.primPhotoTags = None   # Count of photos owned by primary in which primary & secondary are both tagged
		self.otherPhotoTags = None  # Count of photos not owned by primary in which primary & secondary are both tagged
		self.mutuals = None
		self.score = None

	def isBidir(self): # if any of the bidir fields is filled in, return True
		if (self.outPostLikes is not None) or (self.outPostComms is not None) or (self.outStatLikes is not None) or (self.outStatComms is not None):
			return True
		else:
			return False
	def __str__(self):
		ret = ""
		for c in [self.inPostLikes, self.inPostComms, self.inStatLikes, self.inStatComms, self.inWallPosts, self.inWallComms, self.inTags, 
				  self.outPostLikes, self.outPostComms, self.outStatLikes, self.outStatComms, self.outWallPosts, self.outWallComms, self.outTags,
				  self.primPhotoTags, self.otherPhotoTags, self.mutuals]:
			ret += "%2s " % str(c)
		return ret
	def toDict(self):
		u = self.secondary
		d = { 'id': u.id, 'fname': u.fname, 'lname': u.lname, 'name': u.fname + " " + u.lname, 
				'gender': u.gender, 'age': u.age, 'city': u.city, 'state': u.state, 'score': self.score,
				'desc': self.__str__().replace('None', '&Oslash;')
		}
		return d

class EdgeFromCounts(Edge):
	def __init__(self, primInfo, secInfo,
				 inPostLikes, inPostComms, inStatLikes, inStatComms, inWallPosts, inWallComms, inTags,
				 outPostLikes, outPostComms, outStatLikes, outStatComms, outWallPosts, outWallComms, outTags,
				 primPhotoTags, otherPhotoTags, mutuals, score=None):
		self.primary = primInfo
		self.secondary = secInfo
		self.inPostLikes = inPostLikes
		self.inPostComms = inPostComms
		self.inStatLikes = inStatLikes
		self.inStatComms = inStatComms
		self.inWallPosts = inWallPosts
		self.inWallComms = inWallComms
		self.inTags 	 = inTags
		self.outPostLikes = outPostLikes
		self.outPostComms = outPostComms
		self.outStatLikes = outStatLikes
		self.outStatComms = outStatComms
		self.outWallPosts = outWallPosts
		self.outWallComms = outWallComms
		self.outTags	  = outTags
		self.primPhotoTags = primPhotoTags
		self.otherPhotoTags = otherPhotoTags
		self.mutuals = mutuals
		self.score = score

class EdgeStreamless(Edge):
	def __init__(self, userInfo, friendInfo):
		super(EdgeStreamless, self).__init__(self, userInfo, friendInfo)
		self.primPhotoTags = friendInfo.primPhotoTags
		self.otherPhotoTags = friendInfo.otherPhotoTags
		self.mutuals = friendInfo.mutuals
	def isBidir(self):
		return False

class EdgeSC1(EdgeStreamless):
	def __init__(self, userInfo, friendInfo, userStreamCount):
		super(EdgeSC1, self).__init__(self, userInfo, friendInfo)
		self.inPostLikes = userStreamCount.getPostLikes(friendInfo.id)
		self.inPostComms = userStreamCount.getPostComms(friendInfo.id)
		self.inStatLikes = userStreamCount.getStatLikes(friendInfo.id)
		self.inStatComms = userStreamCount.getStatComms(friendInfo.id)
		self.inWallPosts = userStreamCount.getWallPosts(friendInfo.id)
		self.inWallComms = userStreamCount.getWallComms(friendInfo.id)
		self.inTags 	 = userStreamCount.getTags(friendInfo.id)

class EdgeSC2(EdgeSC1):
	def __init__(self, userInfo, friendInfo, userStreamCount, friendStreamCount):
		super(EdgeSC2, self).__init__(self, userInfo, friendInfo, userStreamCount)
		self.outPostLikes = friendStreamCount.getPostLikes(userInfo.id)
		self.outPostComms = friendStreamCount.getPostComms(userInfo.id)
		self.outStatLikes = friendStreamCount.getStatLikes(userInfo.id)
		self.outStatComms = friendStreamCount.getStatComms(userInfo.id)
		self.outWallPosts = friendStreamCount.getWallPosts(userInfo.id)
		self.outWallComms = friendStreamCount.getWallComms(userInfo.id)
		self.outTags 	 = friendStreamCount.getTags(userInfo.id)
	def isBidir(self):
		return True

class EdgeAggregator(Edge):
	def __init__(self, edgesSource, aggregFunc, requireIncoming=True, requireOutgoing=True):
		super(EdgeAggregator, self).__init__(self, None, None)
		if (len(edgesSource) > 0):
			if (requireIncoming):
				self.inPostLikes = aggregFunc([ e.inPostLikes for e in edgesSource ])
				self.inPostComms = aggregFunc([ e.inPostComms for e in edgesSource ])
				self.inStatLikes = aggregFunc([ e.inStatLikes for e in edgesSource ])
				self.inStatComms = aggregFunc([ e.inStatComms for e in edgesSource ])
				self.inWallPosts = aggregFunc([ e.inWallPosts for e in edgesSource ])
				self.inWallComms = aggregFunc([ e.inWallComms for e in edgesSource ])
				self.inTags = aggregFunc([ e.inTags for e in edgesSource ])
			if (requireOutgoing):
				self.outPostLikes = aggregFunc([ e.outPostLikes for e in edgesSource ])
				self.outPostComms = aggregFunc([ e.outPostComms for e in edgesSource ])
				self.outStatLikes = aggregFunc([ e.outStatLikes for e in edgesSource ])
				self.outStatComms = aggregFunc([ e.outStatComms for e in edgesSource ])
				self.outWallPosts = aggregFunc([ e.outWallPosts for e in edgesSource ])
				self.outWallComms = aggregFunc([ e.inPostLikes for e in edgesSource ])
				self.outTags = aggregFunc([ e.outTags for e in edgesSource ])
			self.primPhotoTags = aggregFunc([ e.primPhotoTags for e in edgesSource ])
			self.otherPhotoTags = aggregFunc([ e.otherPhotoTags for e in edgesSource ])
			self.mutuals = aggregFunc([ e.mutuals for e in edgesSource ])
			self.bidir = False not in [ e.isBidir() for e in edgesSource ]  # if all of them are bi, the group is bi
	def isBidir(self):
		return self.bidir



