#!/usr/bin/python
import sys
import time
import datetime
from unidecode import unidecode

class Timer(object):
    """used for inline profiling & debugging


    XXX i can probably die
    """
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
        raise NotImplementedError # what is this intended to do? No stderr please!

def unidecodeSafe(s):
    """util func to deal with None, numbers, and unisuck

    XXX I can probably die

    If `s` is None, returns '?'. Otherwise uses :mod:`unidecode` to produce a reasonable bytestring.

    :arg unicode s: a unicode string to convert to bytes
    :returns: a reasonable-looking ASCII bytestring
    :rtype: str
    :raises ValueError: if s is not unicode or None
    """
    if (s is None):
        return "?"
    elif not isinstance(s, unicode):
        raise TypeError("expected unicode, got %s"%type(s))
    else:
        try:
            return str(s)
        except UnicodeEncodeError:
            return unidecode(s)

class UserInfo(object):
    """basic facebook data from a user's profile

    some attrs may be missing

    """

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
                 str(self.age),
                 unidecodeSafe(self.city),
                 unidecodeSafe(self.state) ]
        return " ".join(rets)

class FriendInfo(UserInfo):
    """same as a UserInfo w/ addtional fields relative to a target user

    target user = idPrimary
    """

    def __init__(self, primId, friendId, first_name, last_name, sex, birthday, city, state, primPhotoTags, otherPhotoTags, mutual_friend_count):
        # XXX replace with super()
        UserInfo.__init__(self, friendId, first_name, last_name, sex, birthday, city, state)
        self.idPrimary = primId
        self.primPhotoTags = primPhotoTags
        self.otherPhotoTags = otherPhotoTags
        self.mutuals = mutual_friend_count

class TokenInfo(object):
    """auth token for a user

    friends never have a token, just primary user

    ownerId: which user this token is for
    expires: when the token expires as datetime string
    """

    def __init__(self, tok, own, app, exp):
        self.tok = tok
        self.ownerId = own
        self.appId = app
        self.expires = exp
    def __str__(self):
        return "%s:%s %s (exp %s)" % (self.appId, self.ownerId, self.tok, self.expires.strftime("%m/%d"))

class EdgeCounts(object):
    """ Stores counts of different interactions of one user on another. In all cases, counts indicate
        the actions of the source user on the target's feed.
    


    """
    def __init__(self, sourceId, targetId,
                 postLikes=None, postComms=None, statLikes=None, statComms=None, wallPosts=None, wallComms=None,
                 tags=None, photoTarg=None, photoOth=None, muts=None):
        self.sourceId = sourceId
        self.targetId = targetId
        self.postLikes = postLikes
        self.postComms = postComms
        self.statLikes = statLikes
        self.statComms = statComms
        self.wallPosts = wallPosts  # posts by source on target's wall
        self.wallComms = wallComms  # comments by target on those posts. These might be considered "outgoing"
                                    #   but are found in the target's stream
        self.tags = tags            # tags of the source in a target's post on the target's wall. Again,
                                    #   might be considered "outgoing" but appear in the target's stream...
        self.photoTarget = photoTarg  # count of photos owned by target in which source & target are both tagged
        self.photoOther = photoOth    # count of photos not owned by target in which source & target are both tagged
        self.mutuals = muts

class Edge(object):
    """relationship between two users

    just a container for other objects in module

    primary: UserInfo
    secondary: UserInfo
    edgeCountsIn: primary to secondary
    edgeCountsOut: secondary to primary
    """

    def __init__(self, primInfo, secInfo, edgeCountsIn, edgeCountsOut=None):
        self.primary = primInfo
        self.secondary = secInfo
        self.countsIn = edgeCountsIn
        self.countsOut = edgeCountsOut
        self.score = None
    def toDict(self):
        u = self.secondary
        d = { 'id': u.id, 'fname': u.fname, 'lname': u.lname, 'name': u.fname + " " + u.lname,
                'gender': u.gender, 'age': u.age, 'city': u.city, 'state': u.state, 'score': self.score,
                'desc': ''
        }
        return d



