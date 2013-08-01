#!/usr/bin/python
"""
.. envvar:: database.use_threads

    should work be done in background threads. Respected by some parts of the code, other modules, etc. and some not?

"""
import sys
import logging
import threading
import MySQLdb as mysql


logger = logging.getLogger(__name__)


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
            sql += ", " + ", ".join(["INDEX(" + c + ")" for c in self.indices])
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
def getUserDb(userId, freshnessDays=36525, freshnessIncludeEdge=False): # 100 years!
    """
    :rtype: datastructs.UserInfo

    freshness - how recent does data need to be? returns None if not fresh enough
    """
    raise NotImplementedError


def getFriendEdgesDb(primId, requireIncoming=False,
        requireOutgoing=False, newerThan=0):
    """return list of datastructs.Edge objects for primaryId user

    """
    raise NotImplementedError


# helper function that may get run in a background thread
def _updateDb(user, token, edges):
    """takes datastructs.* and writes to database
    """
    raise NotImplementedError


def updateDb(user, token, edges, background=False):
    """calls _updateDb maybe in thread

    """
    raise NotImplementedError


def updateFriendEdgesDb(curs, edges):
    """update edges table

    """
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


# helper function that may get run in a background thread
def _writeFaceExclusionsDb(userId, campaignId, contentId, friendIds, reason):
    """update events table

    """
    raise NotImplementedError


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
