#!/usr/bin/python
import sys
import time
import datetime




class Timer:
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

class FriendInfo(UserInfo):
	def __init__(self, primId, friendId, first_name, last_name, sex, birthday, city, state, primPhotoTags, otherPhotoTags, mutual_friend_count):
		UserInfo.__init__(self, friendId, first_name, last_name, sex, birthday, city, state)
		self.idPrimary = primId
		self.primPhotoTags = primPhotoTags
		self.otherPhotoTags = otherPhotoTags
		self.mutuals = mutual_friend_count


class Edge(object):
	def __init__(self, primInfo, secInfo,
					inPostLikes, inPostComms, inStatLikes, inStatComms, inWallPosts, inWallComms, inTags,
					outPostLikes, outPostComms, outStatLikes, outStatComms, outWallPosts, outWallComms, outTags,
					primPhotoTags, otherPhotoTags, mutuals):
		self.primary = primInfo
		self.secondary = secInfo
		self.inPostLikes = inPostLikes
		self.inPostComms = inPostComms
		self.inStatLikes = inStatLikes
		self.inStatComms = inStatComms
		self.inWallPosts = inWallPosts		# Posts by secondary or primary's wall
		self.inWallComms = inWallComms		# Comments by primary on those posts. These might be considered "outgoing" but are found in the primary's stream
		self.inTags 	 = inTags			# Tags of the secondary in a primary's post on the primary's wall. Again, might be considered "outgoing" but appear in the priamry's stream...
		self.outPostLikes = outPostLikes
		self.outPostComms = outPostComms
		self.outStatLikes = outStatLikes
		self.outStatComms = outStatComms
		self.outWallPosts = outWallPosts	# Posts by primary on secondary's wall
		self.outWallComms = outWallComms	# Comments by secondary on those posts
		self.outTags	  = outTags			# Tags of primary in a secondary's post on their wall
		self.primPhotoTags = primPhotoTags	# Count of photos owned by primary in which primary & secondary are both tagged
		self.otherPhotoTags = otherPhotoTags  # Count of photos not owned by primary in which primary & secondary are both tagged
		self.mutuals = mutuals
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
				'gender': u.gender, 'age': u.age, 'city': u.city, 'state': u.state, 'score': self.score
				'desc': self.__str__().replace('None', '&Oslash;')
		}
		return d

class EdgeSC1(Edge):
	def __init__(self, userInfo, friendInfo, userStreamCount):
		self.primary = userInfo
		self.secondary = friendInfo
		self.inPostLikes = userStreamCount.getPostLikes(friendInfo.id)
		self.inPostComms = userStreamCount.getPostComms(friendInfo.id)
		self.inStatLikes = userStreamCount.getStatLikes(friendInfo.id)
		self.inStatComms = userStreamCount.getStatComms(friendInfo.id)
		self.inWallPosts = userStreamCount.getWallPosts(friendInfo.id)
		self.inWallComms = userStreamCount.getWallComms(friendInfo.id)
		self.inTags 	 = userStreamCount.getTags(friendInfo.id)
		self.outPostLikes = None
		self.outPostComms = None
		self.outStatLikes = None
		self.outStatComms = None
		self.outWallPosts = None
		self.outWallComms = None
		self.outTags	  = None
		self.primPhotoTags = friendInfo.primPhotoTags
		self.otherPhotoTags = friendInfo.otherPhotoTags
		self.mutuals = friendInfo.mutuals
		self.score = None
	def isBidir(self):
		return False

class EdgeSC2(Edge):
	def __init__(self, userInfo, friendInfo, userStreamCount, friendStreamCount):
		self.primary = userInfo
		self.secondary = friendInfo
		self.inPostLikes = userStreamCount.getPostLikes(friendInfo.id)
		self.inPostComms = userStreamCount.getPostComms(friendInfo.id)
		self.inStatLikes = userStreamCount.getStatLikes(friendInfo.id)
		self.inStatComms = userStreamCount.getStatComms(friendInfo.id)
		self.inWallPosts = userStreamCount.getWallPosts(friendInfo.id)
		self.inWallComms = userStreamCount.getWallComms(friendInfo.id)
		self.inTags 	 = userStreamCount.getTags(friendInfo.id)
		self.outPostLikes = friendStreamCount.getPostLikes(userInfo.id)
		self.outPostComms = friendStreamCount.getPostComms(userInfo.id)
		self.outStatLikes = friendStreamCount.getStatLikes(userInfo.id)
		self.outStatComms = friendStreamCount.getStatComms(userInfo.id)
		self.outWallPosts = friendStreamCount.getWallPosts(userInfo.id)
		self.outWallComms = friendStreamCount.getWallComms(userInfo.id)
		self.outTags 	 = friendStreamCount.getTags(userInfo.id)
		self.primPhotoTags = friendInfo.primPhotoTags
		self.otherPhotoTags = friendInfo.otherPhotoTags
		self.mutuals = friendInfo.mutuals
		self.score = None
	def isBidir(self):
		return True

