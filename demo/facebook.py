#!/usr/bin/python
import datetime
import urllib2
import datastructs




def dateFromFb(dateStr):
	if (dateStr):
		dateElts = dateStr.split('/')
		if (len(dateElts) == 3): 
			m, d, y = dateElts
			return datetime.date(int(y), int(m), int(d))
	return None

def getUrlFb(url):
	try:
		responseFile = urllib2.urlopen(url, timeout=60)
	except (urllib2.URLError, urllib2.HTTPError) as e: 
		logging.info("error opening url %s: %s" % (url, e.reason))
		raise
	responseJson = json.load(responseFile)
	return responseJson

def getFriendsFb(userId, token):
	tim = datastructs.Timer()
	logging.debug("getting friends for %d" % userId)
	fql = """SELECT uid, first_name, last_name, sex, birthday_date, current_location, mutual_friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = %s)""" % (userId)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	responseJson = getUrlFb(url)
	#sys.stderr.write("responseJson: " + str(responseJson) + "\n\n")

	friends = []
	for rec in responseJson['data']:
		city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
		state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
		f = datastructs.FriendInfo(userId, rec['uid'], rec['first_name'], rec['last_name'], rec['sex'], dateFromFb(rec['birthday_date']), city, state, rec['mutual_friend_count'])
		friends.append(f)
	logging.debug("returning %d friends for %d (%s)" % (len(friends), userId, tim.elapsedPr()))
	return friends

def getUserFb(userId, token):
	fql = """SELECT uid, first_name, last_name, sex, birthday_date, current_location FROM user WHERE uid=%s""" % (userId)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	responseJson = getUrlFb(url)
	rec = responseJson['data'][0]
	city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
	state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
	user = datastructs.UserInfo(rec['uid'], rec['first_name'], rec['last_name'], rec['sex'], dateFromFb(rec['birthday_date']), city, state)
	return user







# class ThreadStreamReader(threading.Thread):
