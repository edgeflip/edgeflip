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
	def __init__(self, primId, friendId, first_name, last_name, sex, birthday, city, state, mutual_friend_count):
		UserInfo.__init__(self, friendId, first_name, last_name, sex, birthday, city, state)
		self.idPrimary = primId
		self.mutuals = mutual_friend_count


class Edge(object):
	def __init__(self, primInfo, secInfo,
					inPostLikes, inPostComms, inStatLikes, inStatComms, 
					outPostLikes, outPostComms, outStatLikes, outStatComms, 
					mutuals):
		self.primary = primInfo
		self.secondary = secInfo
		self.inPostLikes = inPostLikes
		self.inPostComms = inPostComms
		self.inStatLikes = inStatLikes
		self.inStatComms = inStatComms
		self.outPostLikes = outPostLikes
		self.outPostComms = outPostComms
		self.outStatLikes = outStatLikes
		self.outStatComms = outStatComms
		self.mutuals = mutuals
		self.score = None
	def __str__(self):
		ret = ""
		for c in[self.inPostLikes, self.inPostComms, self.inStatLikes, self.inStatComms, self.outPostLikes, self.outPostComms, self.outStatLikes, self.outStatComms, self.mutuals]:
			ret += "%2s " % str(c)
		return ret
		
class EdgeSC1(Edge):
	def __init__(self, userInfo, friendInfo, userStreamCount):
		self.primary = userInfo
		self.secondary = friendInfo
		self.inPostLikes = userStreamCount.getPostLikes(friendInfo.id)
		self.inPostComms = userStreamCount.getPostComms(friendInfo.id)
		self.inStatLikes = userStreamCount.getStatLikes(friendInfo.id)
		self.inStatComms = userStreamCount.getStatComms(friendInfo.id)
		self.outPostLikes = None
		self.outPostComms = None
		self.outStatLikes = None
		self.outStatComms = None
		self.mutuals = friendInfo.mutuals
		self.score = None

class EdgeSC2(Edge):
	def __init__(self, userInfo, friendInfo, userStreamCount, friendStreamCount):
		self.primary = userInfo
		self.secondary = friendInfo
		self.inPostLikes = userStreamCount.getPostLikes(friendInfo.id)
		self.inPostComms = userStreamCount.getPostComms(friendInfo.id)
		self.inStatLikes = userStreamCount.getStatLikes(friendInfo.id)
		self.inStatComms = userStreamCount.getStatComms(friendInfo.id)
		self.outPostLikes = friendStreamCount.getPostLikes(userInfo.id)
		self.outPostComms = friendStreamCount.getPostComms(userInfo.id)
		self.outStatLikes = friendStreamCount.getStatLikes(userInfo.id)
		self.outStatComms = friendStreamCount.getStatComms(userInfo.id)
		self.mutuals = friendInfo.mutuals
		self.score = None
