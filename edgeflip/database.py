#!/usr/bin/python
"""
.. envvar:: database.use_threads

    should work be done in background threads. Respected by some parts of the code, other modules, etc. and some not?
"""

import sys
import time
import logging
import datetime
import threading
import MySQLdb as mysql
import flask

from . import datastructs
from .settings import config

logger = logging.getLogger(__name__)

# `threading.local` for db connections created outside of flask. gross.
_non_flask_threadlocal = threading.local()

def _make_connection():
    """makes a connection to mysql, based on configuration. For internal use.
    
    :rtype: mysql connection object
    
    """
    
    return mysql.connect(config['dbhost'], config['dbuser'], config['dbpass'], config['dbname'], charset="utf8", use_unicode=True)

def getConn():
    """return a connection for this thread.
    
    All calls from the same thread return the same connection object. Do not save these or pass them around (esp. b/w threads!).
    
    You are responsible for managing the state of your connection; it may be cleaned up (rollback()'d , etc.) on thread destruction, but you shouldn't rely on such things.
    """
    try:
        conn = flask.g.conn
    except RuntimeError as err:        
        # xxx gross, le sigh
        if err.message != "working outside of request context":
            raise
        else:
            # we are in a random thread the code spawned off from
            # $DIETY knows where. Here, have a connection:
            logger.debug("You made a database connection from random thread %d, and should feel bad about it.", threading.current_thread().ident)
            try:
                return _non_flask_threadlocal.conn
            except AttributeError:                
                conn = _non_flask_threadlocal.conn = _make_connection()
    except AttributeError:
        # we are in flask-managed thread, which is nice.
        # create a new connection & save it for reuse
        conn = flask.g.conn = _make_connection()
    
    return conn

class Table(object):
    """represents a Table

    """
    def __init__(self, name, cols=None, indices=None, key=None, otherStmts=None):
        cols = cols if cols is not None else []
        indices = indices if indices is not None else []
        key = key if key is not None else []
        otherStmts = otherStmts if otherStmts is not None else []
         
        self.name = name
        self.colTups = []
        self.addCols(cols)
        self.indices = []
        for col in indices:
            self.addIndex(col)
        self.keyCols = key
        self.otherStmts = otherStmts
    def addCols(self, cTups):  # colTups are (colName, colType) or (colName, colType, colDefault)
        for cTup in cTups:
            if (len(cTup) == 2):
                cTup = (cTup[0], cTup[1], None)
            self.colTups.append(cTup)
    def addCol(self, colName, colType, colDefault=None):
        self.addCols([(colName, colType, colDefault)])
    def addIndex(self, colName):
        self.indices.append(colName)
    def setKey(self, cols):
        self.keyCols = cols
    def getKey(self):
        return self.keyCols
    def sqlCreate(self):
        sys.stderr.write("colTups: " + str(self.colTups) + "\n")
        sql = "CREATE TABLE " + self.name
        sql += " ("
        colSqls = []
        for colName, colType, colDefault in self.colTups:
            colSql = colName + " " + colType
            if (colDefault is not None):
                colSql += " DEFAULT " + colDefault
            colSqls.append(colSql)
        sql += ", ".join(colSqls)
        if (self.indices):  # , INDEX(colA), INDEX(colB)
            sql += ", " + ", ".join([ "INDEX(" + c + ")" for c in self.indices ])
        if (self.keyCols):  # PRIMARY KEY (colA, colB)
            sql += ", PRIMARY KEY (" + ", ".join(self.keyCols) + ")"
        sql += ") "
        return sql
    def sqlDrop(self):
        return "DROP TABLE IF EXISTS " + self.name

TABLES = dict()

# datastructs.UserInfo
TABLES['users'] =     Table(name='users',
                            cols=[
                                ('fbid', 'BIGINT'),
                                ('fname', 'VARCHAR(128)'),
                                ('lname', 'VARCHAR(128)'),
                                ('email', 'VARCHAR(256)'),
                                ('gender', 'VARCHAR(8)'),
                                ('birthday', 'DATE'),
                                ('city', 'VARCHAR(32)'),
                                ('state', 'VARCHAR(32)'),
                                ('updated', 'TIMESTAMP', 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
                            ],
                            key=['fbid'])

# datastructs.Tokens
TABLES['tokens'] =    Table(name='tokens',
                            cols=[
                                ('fbid', 'BIGINT'),
                                ('appid', 'BIGINT'),
                                ('ownerid', 'BIGINT'),
                                ('token', 'VARCHAR(512)'),
                                ('expires', 'DATETIME'),
                                ('updated', 'TIMESTAMP', 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
                            ],
                            key=['fbid', 'appid', 'ownerid'])

# raw data behind datastructs.Edge*
# Given how we pull data from this table, it's really very helpful to have unique keys with both column orders
# (ideally, (fbid_target, fbid_source) would be the primary given that we'll more often specify fbid_target in
# a where clause in real time (eg if only grabbing px3 or 4), but probably not a huge deal)
TABLES['edges'] =     Table(name='edges',
                            cols=[
                                ('fbid_source', 'BIGINT'),
                                ('fbid_target', 'BIGINT'),
                                ('post_likes', 'INTEGER'),
                                ('post_comms', 'INTEGER'),
                                ('stat_likes', 'INTEGER'),
                                ('stat_comms', 'INTEGER'),
                                ('wall_posts', 'INTEGER'),
                                ('wall_comms', 'INTEGER'),
                                ('tags', 'INTEGER'),
                                ('photos_target', 'INTEGER'),
                                ('photos_other', 'INTEGER'),
                                ('mut_friends', 'INTEGER'),
                                ('updated', 'TIMESTAMP', 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
                            ],
                            key=['fbid_source', 'fbid_target'],
                            otherStmts=["CREATE UNIQUE INDEX targ_source ON edges (fbid_target, fbid_source)"])

# user activity tracking
TABLES['events'] =    Table(name='events',
                            cols=[
                                ('session_id', 'VARCHAR(128)'),
                                ('campaign_id', 'INT'),
                                ('content_id', 'INT'),
                                ('ip', 'VARCHAR(32)'),
                                ('fbid', 'BIGINT'),
                                ('friend_fbid', 'BIGINT'),
                                ('type', 'VARCHAR(64)'),
                                ('appid', 'BIGINT'),
                                ('content', 'VARCHAR(128)'),
                                ('activity_id', 'BIGINT'),
                                ('updated', 'TIMESTAMP', 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
                            ],
                            indices=['session_id', 'campaign_id', 'content_id', 'fbid', 'friend_fbid', 'activity_id'])

# The actual messages shared on facebook
TABLES['share_messages'] =  Table(name='share_messages',
                                  cols = [
                                        ('activity_id', 'BIGINT'),
                                        ('fbid', 'BIGINT'),
                                        ('campaign_id', 'INT'),
                                        ('content_id', 'INT'),
                                        ('message', 'VARCHAR(4096)'),
                                        ('updated', 'TIMESTAMP', 'CURRENT_TIMESTAMP')
                                  ],
                                  indices=['fbid', 'campaign_id', 'content_id'],
                                  key=['activity_id'])

# Secondaries who should be excluded from future share suggestions
TABLES['face_exclusions'] =     Table(name='face_exclusions',
                                      cols=[
                                            ('fbid', 'BIGINT'),
                                            ('campaign_id', 'INT'),
                                            ('content_id', 'INT'),
                                            ('friend_fbid', 'BIGINT'),
                                            ('reason', 'VARCHAR(512)'),
                                            ('updated', 'TIMESTAMP', 'CURRENT_TIMESTAMP')
                                      ],
                                      key=['fbid', 'campaign_id', 'content_id', 'friend_fbid'])


# Reset the DB by dropping and recreating tables
def dbSetup(tableKeys=None):
    """creates tables"""

    conn = getConn()
    curs = conn.cursor()
    if (tableKeys is None):
        tableKeys = TABLES.keys()
    for tabName in tableKeys:
        tab = TABLES[tabName]
        sql = tab.sqlDrop()
        sys.stderr.write(sql + "\n")
        curs.execute(sql)
        sql = tab.sqlCreate()
        sys.stderr.write(sql + "\n")
        curs.execute(sql)
        for stmt in tab.otherStmts:
            curs.execute(stmt)
    conn.commit()

def getUserTokenDb(userId, appId):
    """grab the "best" token from the tokens table

    For now, it simply grabs all non-expired tokens and orders them by
    primary status (whether owner matches user), followed by updated date.

    :rtype: datastructs.TokenInfo
    """
    conn = getConn()
    curs = conn.cursor()
    ts = time.time()
    sql = "SELECT token, ownerid, unix_timestamp(expires) FROM tokens WHERE fbid=%s AND unix_timestamp(expires)>%s AND appid=%s "
    params = (userId, ts, appId)
    sql += "ORDER BY (CASE WHEN fbid=ownerid THEN 0 ELSE 1 END), updated DESC"
    curs.execute(sql, params)
    rec = curs.fetchone()
    if (rec is None):
        ret = None
    else:
        expDate = datetime.datetime.utcfromtimestamp(rec[2])
        ret = datastructs.TokenInfo(rec[0], rec[1], appId, expDate)
    return ret


def getUserDb(userId, freshnessDays=36525, freshnessIncludeEdge=False): # 100 years!
    """
    :rtype: datastructs.UserInfo

    freshness - how recent does data need to be? returns None if not fresh enough
    """

    conn = getConn()

    freshnessDate = datetime.datetime.utcnow() - datetime.timedelta(days=freshnessDays)
    logger.debug("getting user %s, freshness date is %s (GMT)" % (userId, freshnessDate.strftime("%Y-%m-%d %H:%M:%S")))
    sql = """SELECT fbid, fname, lname, email, gender, birthday, city, state, unix_timestamp(updated) FROM users WHERE fbid=%s"""

    curs = conn.cursor()
    curs.execute(sql, (userId,))
    rec = curs.fetchone()
    if (rec is None):
        return None
    else:
        fbid, fname, lname, email, gender, birthday, city, state, updated = rec
        updated = datetime.datetime.utcfromtimestamp(updated)
        logger.debug("getting user %s, update date is %s (GMT)" % (userId, updated.strftime("%Y-%m-%d %H:%M:%S")))

        if (updated <= freshnessDate):
            return None
        else:
            """We want freshnessIncludeEdge to go away! (should just get the edges & check them separately)"""
            if (freshnessIncludeEdge):
                curs.execute("SELECT min(unix_timestamp(updated)) as freshnessEdge FROM edges WHERE fbid_source=%s OR fbid_target=%s", (userId, userId))
                rec = curs.fetchone()

                updatedEdge = datetime.datetime.utcfromtimestamp(rec[0])
                if (updatedEdge is None) or (updatedEdge < freshnessDate):
                    return None

        # if we made it here, we're fresh
        return datastructs.UserInfo(fbid, fname, lname, email, gender, birthday, city, state)


def getFriendEdgesDb(primId, requireOutgoing=False, maxAge=None):
    """return list of datastructs.Edge objects for primaryId user

    """
    assert isinstance(maxAge, (datetime.timedelta, types.NoneType))
    dt = datetime.datetime.now() - maxAge if maxAge is not None else datetime.datetime.now()
    minEpoch = time.mktime(dt.utctimetuple())

    conn = getConn()

    edges = []  # list of edges to be returned
    primary = getUserDb(primId)

    curs = conn.cursor()
    sqlSelect = """
            SELECT e.fbid_source, e.fbid_target,
                    e.post_likes, e.post_comms, e.stat_likes, e.stat_comms, 
                    e.wall_posts, e.wall_comms, e.tags, 
                    e.photos_target, e.photos_other, e.mut_friends, 
                    unix_timestamp(e.updated),
                    u.fname, u.lname, u.email, u.gender, u.birthday, u.city, u.state
            FROM edges e
            JOIN users u
    """

    sql = sqlSelect + \
        " ON e.fbid_source = u.fbid" + \
        " WHERE unix_timestamp(e.updated)>%s AND e.fbid_target=%s"
    params = (minEpoch, primId)
    secId_edgeCountsIn = {}
    secId_userInfo = {}
    curs.execute(sql, params)
    for rec in curs: # here, the secondary is the source, primary is the target
        secId, primId, iPstLk, iPstCm, iStLk, iStCm, \
            iWaPst, iWaCm, iTags, iPhOwn, iPhOth, iMuts, iUpdated, \
            fname, lname, email, gender, birthday, city, state = rec
        edgeCountsIn = datastructs.EdgeCounts(secId, primId,
                                              iPstLk, iPstCm, iStLk, iStCm, iWaPst, iWaCm,
                                              iTags, iPhOwn, iPhOth, iMuts)
        secInfo = datastructs.UserInfo(secId, fname, lname, email, gender, birthday, city, state)

        secId_edgeCountsIn[secId] = edgeCountsIn
        secId_userInfo[secId] = secInfo

    if (not requireOutgoing):
        for secId, edgeCountsIn in secId_edgeCountsIn.items():
            logger.debug("Got secondary info & incoming edge for %s----%s from the database.", primary.id, secId)
            edges.append(datastructs.Edge(primary, secId_userInfo[secId], edgeCountsIn, None))

    else:
        sql = sqlSelect + \
            " ON e.fbid_target = u.fbid" + \
            " WHERE unix_timestamp(e.updated)>%s AND e.fbid_source=%s"
        params = (minEpoch, primId)
        curs.execute(sql, params)
        for rec in curs: # here, primary is the source, secondary is target
            primId, secId, oPstLk, oPstCm, oStLk, oStCm, \
                oWaPst, oWaCm, oTags, oPhOwn, oPhOth, oMuts, oUpdated, \
                fname, lname, email, gender, birthday, city, state = rec
            edgeCountsOut = datastructs.EdgeCounts(primId, secId,
                                                   oPstLk, oPstCm, oStLk, oStCm, oWaPst, oWaCm,
                                                   oTags, oPhOwn, oPhOth, oMuts)
            secondary = datastructs.UserInfo(secId, fname, lname, email, gender, birthday, city, state)

            # zzz This will simply ignore edges where we've crawled the outgoing edge but not 
            #     the incoming one (eg, with the current primary as someone else's secondary) 
            #     That could happen either if this primary is totally new OR if it's a new 
            #     friend who came in as a primary after friending the current primary.
            edgeCountsIn = secId_edgeCountsIn.get(secId)
            if edgeCountsIn is not None:
                logger.debug("Got secondary info & bidirectional edge for %s----%s from the database.", primary.id, secId)
                edges.append(datastructs.Edge(primary, secondary, edgeCountsIn, edgeCountsOut))
            else:
                logger.warning("Edge skipped: no incoming data found for %s----%s.", primary.id, secId)
    return edges

# helper function that may get run in a background thread
def _updateDb(user, token, edges):
    """takes datastructs.* and writes to database
    """
    tim = datastructs.Timer()
    conn = getConn()
    curs = conn.cursor()
    
    try:
        updateTokensDb(curs, [user], token)
        updateUsersDb(curs, [user])
        tCount = updateTokensDb(curs, [e.secondary for e in edges], token)
        fCount = updateUsersDb(curs, [e.secondary for e in edges])
        eCount = updateFriendEdgesDb(curs, edges)
        conn.commit()
    except:
        conn.rollback()
        raise
    
    logger.debug("_updateDB() thread %d updated %d friends, %d tokens, %d edges for user %d (took %s)" %
                    (threading.current_thread().ident, fCount, tCount, eCount, user.id, tim.elapsedPr()))
    return eCount


def updateDb(user, token, edges, background=False):
    """calls _updateDb maybe in thread

    """

    if (background):
        t = threading.Thread(target=_updateDb, args=(user, token, edges))
        t.daemon = False
        t.start()
        logger.debug("updateDb() spawning background thread %d for user %d", t.ident, user.id)
        return 0
    else:
        logger.debug("updateDb() foreground thread %d for user %d", threading.current_thread().ident, user.id)
        return _updateDb(user, token, edges)

def updateFriendEdgesDb(curs, edges):
    """update edges table

    """

    writeCount = 0
    for e in edges:
        for counts in [e.countsIn, e.countsOut]:
            if (counts is not None):
                col_val = {
                    'fbid_source': counts.sourceId,
                    'fbid_target': counts.targetId,
                    'post_likes': counts.postLikes,
                    'post_comms': counts.postComms,
                    'stat_likes': counts.statLikes,
                    'stat_comms': counts.statComms,
                    'wall_posts': counts.wallPosts,
                    'wall_comms': counts.wallComms,
                    'tags': counts.tags,
                    'photos_target': counts.photoTarget,
                    'photos_other': counts.photoOther,
                    'mut_friends': counts.mutuals,
                    'updated': None     # Force DB to change updated to current_timestamp 
                                        # even if rest of record is identical. Depends on
                                        # MySQL handling of NULLs in timestamps and feels
                                        # a bit ugly...
                }
                writeCount += upsert(curs, "edges", col_val)
    return writeCount


def updateUsersDb(curs, users):
    """update users table

    """

    updateCount = 0
    for u in users:
        col_val = { 
            'fname': u.fname, 
            'lname': u.lname,
            'email': u.email,
            'gender': u.gender, 
            'birthday': u.birthday,
            'city': u.city, 
            'state': u.state    
        }
        # Only include columns with non-null (or empty/zero) values
        # to ensure a NULL can never overwrite a non-null
        col_val = { k : v for k,v in col_val.items() if v }
        col_val['fbid'] = u.id
        col_val['updated'] = None   # Force DB to change updated to current_timestamp 
                                    # even if rest of record is identical. Depends on
                                    # MySQL handling of NULLs in timestamps and feels
                                    # a bit ugly...
        updateCount += upsert(curs, 'users', col_val)
    return updateCount

def updateTokensDb(curs, users, token):
    """update tokens table"""

    insertedTokens = 0
    for user in users:
        col_val = {
            'fbid': user.id,
            'appid': token.appId,
            'ownerid': token.ownerId,
            'token':token.tok,
            'expires': token.expires,
            'updated' : None    # Force DB to change updated to current_timestamp 
                                # even if rest of record is identical. Depends on
                                # MySQL handling of NULLs in timestamps and feels
                                # a bit ugly...
        }
        insertedTokens += upsert(curs, "tokens", col_val)
    return insertedTokens

#todo: implement colsCoalesce
def upsert(curs, table, col_val, coalesceCols=None):
    """perform an insert or update in one statement to avoid race condtions and allow for queued sql writes

    generates sql like:
        INSERT INTO tableguy (keycol, valcol1, valcol2) VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE valcol1=%s, valcol2=%s
    which must be given params:
        (keyval, val1, val2, val1, val2)

    keyCols specifies key columns
    coalesceCols specifies columns that should be coalesced instead of overwritten (TODO)
    """
    keyColNames = TABLES[table].getKey()
    valColNames = [ c for c in col_val.keys() if c not in set(keyColNames) ]
    keyColVals = [ col_val[c] for c in keyColNames ]
    valColVals = [ col_val[c] for c in valColNames ]
    keyColWilds = [ '%s' for c in keyColNames ]
    valColWilds = [ '%s' for c in valColNames ]

    # SQLi
    sql = "INSERT INTO " + table + " (" + ", ".join(keyColNames + valColNames) + ") "
    sql += "VALUES (" + ", ".join(keyColWilds + valColWilds) + ") "
    sql += "ON DUPLICATE KEY UPDATE " + ", ".join([ c + "=%s" for c in valColNames])
    params = keyColVals + valColVals + valColVals
    logger.debug("upsert sql: " + sql + " " + str(params))

    try:
        curs.execute(sql, params)
        curs.connection.commit() #zzz if we're going to commit, we should prob be passing the connection around
    except mysql.Error as e:
        logger.error("error upserting: " + str(e))
        return 0

    # zzz curs.rowcount returns 2 for a single "upsert" if it updates, 1 if it inserts
    #     but we only want to count either case as a single affected row...
    #     (see: http://dev.mysql.com/doc/refman/5.5/en/insert-on-duplicate.html)
    return 1 if curs.rowcount else 0



# helper function that may get run in a background thread
def _writeEventsDb(sessionId, campaignId, contentId, ip, userId, friendIds, eventType, appId, content, activityId):
    """update events table

    """

    tim = datastructs.Timer()
    conn = getConn()
    curs = conn.cursor()

    rows = [{'sessionId': sessionId, 'campaignId' : campaignId, 'contentId' : contentId,
             'ip': ip, 'userId': userId, 'friendId': friendId,
             'eventType': eventType, 'appId': appId, 'content': content, 'activityId': activityId
            } for friendId in friendIds]
    sql = """INSERT INTO events (session_id, campaign_id, content_id, ip, fbid, friend_fbid, type, appid, content, activity_id)
                VALUES (%(sessionId)s, %(campaignId)s, %(contentId)s, %(ip)s, %(userId)s, %(friendId)s, %(eventType)s, %(appId)s, %(content)s, %(activityId)s) """

    insertCount = 0
    for row in rows:
        curs.execute(sql, row)
        conn.commit()
        insertCount += 1

    logger.debug("_writeEventsDb() thread %d updated %d %s event(s) from session %s", threading.current_thread().ident, insertCount, eventType, sessionId)

    return insertCount

def writeEventsDb(sessionId, campaignId, contentId, ip, userId, friendIds, eventType, appId, content, activityId, background=False):
    """calls _writeEventsDb maybe in a thread

    """
    # friendIds should be a list (as we may want to write multiple shares or suppressions at the same time)
    if (background):
        t = threading.Thread(target=_writeEventsDb,
                             args=(sessionId, campaignId, contentId, ip, userId, friendIds, eventType, appId, content, activityId))
        t.daemon = False
        t.start()
        logger.debug("writeEventsDb() spawning background thread %d for %s event from session %s", t.ident, eventType, sessionId)
        return 0
    else:
        logger.debug("writeEventsDb() foreground thread %d for %s event from session %s", threading.current_thread().ident, eventType, sessionId)
        return _writeEventsDb(sessionId, campaignId, contentId, ip, userId, friendIds, eventType, appId, content, activityId)


# helper function that may get run in a background thread
def _writeShareMsgDb(activityId, userId, campaignId, contentId, shareMsg):
    """update share_messages table

    """

    conn = getConn()
    curs = conn.cursor()

    row = {
            'activityId': activityId, 'userId': userId, 
            'campaignId': campaignId, 'contentId': contentId,
            'shareMsg': shareMsg
          }
    sql = """INSERT IGNORE INTO share_messages (activity_id, fbid, campaign_id, content_id, message)
                VALUES (%(activityId)s, %(userId)s, %(campaignId)s, %(contentId)s, %(shareMsg)s) """

    curs.execute(sql, row)
    conn.commit()
    insertCount = 1

    logger.debug("_writeShareMsgDb() thread %d wrote share message for FB action %s", threading.current_thread().ident, activityId)

    return insertCount

def writeShareMsgDb(activityId, userId, campaignId, contentId, shareMsg, background=False):
    """calls _writeShareMsgDb maybe in a thread

    """

    if (background):
        t = threading.Thread(target=_writeShareMsgDb,
                             args=(activityId, userId, campaignId, contentId, shareMsg))
        t.daemon = False
        t.start()
        logger.debug("writeShareMsgDb() spawning background thread %d for FB action %s", t.ident, activityId)
        return 0
    else:
        logger.debug("writeShareMsgDb() foreground thread %d for FB action %s", threading.current_thread().ident, activityId)
        return _writeShareMsgDb(activityId, userId, campaignId, contentId, shareMsg)


def getFaceExclusionsDb(userId, campaignId, contentId):
    """returns the set of friends to not show as faces for a given primary user
        sharing a certain piece of content under a certain campaign"""

    conn = getConn()
    curs = conn.cursor()

    sql = "SELECT friend_fbid FROM face_exclusions WHERE fbid=%s AND campaign_id=%s AND content_id=%s"
    vals = [userId, campaignId, contentId]

    curs.execute(sql, vals)
    res = curs.fetchall()
    conn.commit()

    excludeFriends = set([rec[0] for rec in res])
    return excludeFriends

# helper function that may get run in a background thread
def _writeFaceExclusionsDb(userId, campaignId, contentId, friendIds, reason):
    """update events table

    """

    # zzz Could run into trouble here with the insert-ignores in the case where
    #     someone suppressed a friend, but then later added them manually. The
    #     front-end behavior will still be correct, but we'll only show the initial
    #     reason why they should be excluded in this table. Probably not a big deal,
    #     but worth keeping in mind that this table is NOT a complete record of all
    #     the shares and suppressions -- that lives in the events table.

    conn = getConn()
    curs = conn.cursor()

    rows = [{
             'userId': userId, 'campaignId' : campaignId, 'contentId' : contentId,
             'friendId': friendId, 'reason': reason
            } for friendId in friendIds]
    sql = """INSERT IGNORE INTO face_exclusions (fbid, campaign_id, content_id, friend_fbid, reason)
                VALUES (%(userId)s, %(campaignId)s, %(contentId)s, %(friendId)s, %(reason)s) """

    insertCount = 0
    for row in rows:
        curs.execute(sql, row)
        conn.commit()
        insertCount += 1

    logger.debug("_writeFaceExclusionsDb() thread %d updated %d %s exclusions from user %s", threading.current_thread().ident, insertCount, reason, userId)

    return insertCount

def writeFaceExclusionsDb(userId, campaignId, contentId, friendIds, reason, background=False):
    """calls _writeFaceExclusionsDb maybe in a thread

    """
    # friendIds should be a list (as we may want to write multiple shares or suppressions at the same time)
    # reason should be 'shared' or 'suppressed'. In principle, could be something like 'shown X times but never shared' 
    #       (though this would take a lot more juggling with who is being shown in the current session!)
    if (background):
        t = threading.Thread(target=_writeFaceExclusionsDb,
                             args=(userId, campaignId, contentId, friendIds, reason))
        t.daemon = False
        t.start()
        logger.debug("writeFaceExclusionsDb() spawning background thread %d for %s exclusions from user %s", t.ident, reason, userId)
        return 0
    else:
        logger.debug("writeFaceExclusionsDb() foreground thread %d for %s exclusions from user %s", threading.current_thread().ident, reason, userId)
        return _writeFaceExclusionsDb(userId, campaignId, contentId, friendIds, reason)

