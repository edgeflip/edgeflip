#!/usr/bin/python
import sys

from . import database
from . import datastructs

import logging

from . import config as conf
config = conf.getConfig(includeDefaults=True)



# class EdgeAggregator(Edge):
class EdgeAggregator(object):
    def __init__(self, edgesSource, aggregFunc, requireIncoming=True, requireOutgoing=True):
        # Edge.__init__(self, None, None)
        if (len(edgesSource) > 0):

            # these are defined even if requireIncoming is False, even though they are stored in countsIn
            self.inPhotoTarget = aggregFunc([ e.countsIn.photoTarget for e in edgesSource ])
            self.inPhotoOther = aggregFunc([ e.countsIn.photoOther for e in edgesSource ])
            self.inMutuals = aggregFunc([ e.countsIn.mutuals for e in edgesSource ])

            if (requireIncoming):
                self.inPostLikes = aggregFunc([ e.countsIn.postLikes for e in edgesSource ])
                self.inPostComms = aggregFunc([ e.countsIn.postComms for e in edgesSource ])
                self.inStatLikes = aggregFunc([ e.countsIn.statLikes for e in edgesSource ])
                self.inStatComms = aggregFunc([ e.countsIn.statComms for e in edgesSource ])
                self.inWallPosts = aggregFunc([ e.countsIn.wallPosts for e in edgesSource ])
                self.inWallComms = aggregFunc([ e.countsIn.wallComms for e in edgesSource ])
                self.inTags = aggregFunc([ e.countsIn.tags for e in edgesSource ])

            if (requireOutgoing):
                self.outPostLikes = aggregFunc([ e.countsOut.postLikes for e in edgesSource ])
                self.outPostComms = aggregFunc([ e.countsOut.postComms for e in edgesSource ])
                self.outStatLikes = aggregFunc([ e.countsOut.statLikes for e in edgesSource ])
                self.outStatComms = aggregFunc([ e.countsOut.statComms for e in edgesSource ])
                self.outWallPosts = aggregFunc([ e.countsOut.wallPosts for e in edgesSource ])
                self.outWallComms = aggregFunc([ e.countsOut.wallComms for e in edgesSource ])
                self.outTags = aggregFunc([ e.countsOut.tags for e in edgesSource ])
                self.outPhotoTarget = aggregFunc([ e.countsOut.photoTarget for e in edgesSource ])
                self.outPhotoOther = aggregFunc([ e.countsOut.photoOther for e in edgesSource ])
                self.outMutuals = aggregFunc([ e.countsOut.mutuals for e in edgesSource ])


def prox(e, eMax):
    countMaxWeightTups = []
    if (e.countsIn is not None):
        countMaxWeightTups.extend([
            # px3
            (e.countsIn.mutuals, eMax.inMutuals, 0.5),
            (e.countsIn.photoTarget, eMax.inPhotoTarget, 2.0),
            (e.countsIn.photoOther, eMax.inPhotoOther, 1.0),

            # px4
            (e.countsIn.postLikes, eMax.inPostLikes, 1.0),
            (e.countsIn.postComms, eMax.inPostComms, 1.0),
            (e.countsIn.statLikes, eMax.inStatLikes, 2.0),
            (e.countsIn.statComms, eMax.inStatComms, 1.0),
            (e.countsIn.wallPosts, eMax.inWallPosts, 1.0),        # guessed weight
            (e.countsIn.wallComms, eMax.inWallComms, 1.0),        # guessed weight
            (e.countsIn.tags, eMax.inTags, 1.0)
        ])

    if (e.countsOut is not None):
        countMaxWeightTups.extend([
            # px3
            (e.countsOut.mutuals, eMax.outMutuals, 0.5),
            (e.countsOut.photoTarget, eMax.outPhotoTarget, 1.0),
            (e.countsOut.photoOther, eMax.outPhotoOther, 1.0),

            # px5
            (e.countsOut.postLikes, eMax.outPostLikes, 2.0),
            (e.countsOut.postComms, eMax.outPostComms, 3.0),
            (e.countsOut.statLikes, eMax.outStatLikes, 2.0),
            (e.countsOut.statComms, eMax.outStatComms, 16.0),
            (e.countsOut.wallPosts, eMax.outWallPosts, 2.0),    # guessed weight
            (e.countsOut.wallComms, eMax.outWallComms, 3.0),    # guessed weight
            (e.countsOut.tags, eMax.outTags, 1.0)
        ])

    pxTotal = 0.0
    weightTotal = 0.0
    for count, countMax, weight in countMaxWeightTups:
        if (countMax):
            pxTotal += float(count)/countMax*weight
            weightTotal += weight
    return pxTotal / weightTotal                

def getFriendRanking(userId, edges, requireIncoming=True, requireOutgoing=True):
    logging.info("ranking %d edges", len(edges))
    edgesMax = EdgeAggregator(edges, max, requireIncoming, requireOutgoing)
    # score each one and store it on the edge
    for e in edges:
        e.score = prox(e, edgesMax)
    return sorted(edges, key=lambda x: x.score, reverse=True)

def getFriendRankingDb(conn, userId, requireOutgoing=True):
    edgesDb = database.getFriendEdgesDb(conn, userId, requireOutgoing)
    return getFriendRanking(userId, edgesDb, requireOutgoing)

def getFriendRankingBestAvail(userId, edgesPart, edgesFull, threshold=0.5):
    edgeCountPart = len(edgesPart)
    edgeCountFull = len(edgesFull)
    if (edgeCountPart*threshold > edgeCountFull):
        return getFriendRanking(userId, edgesPart, requireOutgoing=False)
    else:
        return getFriendRanking(userId, edgesFull, requireOutgoing=True)

def getFriendRankingBestAvailDb(conn, userId, threshold=0.5):
    edgesPart = database.getFriendEdgesDb(conn, userId, requireOutgoing=False)
    edgesFull = database.getFriendEdgesDb(conn, userId, requireOutgoing=True)
    return getFriendRankingBestAvail(userId, edgesPart, edgesFull, threshold)




#####################################################

if (__name__ == '__main__'):
    import facebook

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

    REQUIRE_OUTGOING = False
    UPDATE_DB = True

    userId = int(sys.argv[1])
    user_info = dict([ (t[0], (t[1], t[2])) for t in USER_TUPS ])
    nam, tok = user_info[userId]

    if (UPDATE_DB):
        conn = database.getConn()
        curs = conn.cursor()
        user = facebook.getUserFb(userId, tok)
        database.updateUserDb(curs, user, tok, None)
        edges = facebook.getFriendEdgesFb(userId, tok, requireIncoming=True, requireOutgoing=REQUIRE_OUTGOING)
        newCount = database.updateFriendEdgesDb(userId, tok, edges)
        logging.debug("inserted %d new edges\n" % newCount)
        conn.close()

    for friend in getFriendRankingDb(None, userId, REQUIRE_OUTGOING):
        name = "%s %s" % (friend.fname, friend.lname)
        sys.stderr.write("friend %20s %32s\n" % (friend.id, name))

