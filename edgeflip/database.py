#!/usr/bin/python
import sys
import time
import logging
import datetime
import threading
import MySQLdb as mysql

from . import datastructs
# from . import database_rds as db # modify this to swtch db implementations
from . import config as conf

config = conf.getConfig(includeDefaults=True)




def getConn():
    #return db.getConn()
    return mysql.connect(config['dbhost'], config['dbuser'], config['dbpass'], config['dbname'], charset="utf8", use_unicode=True)


class Table(object):
    def __init__(self, name, cols=[], indices=[], key=[]):
        self.name = name
        self.colTups = []
        self.addCols(cols)
        self.indices = []
        for col in indices:
            self.addIndex(col)
        self.keyCols = key
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

TABLES['users'] =     Table(name='users',
                            cols=[
                                ('fbid', 'BIGINT'),
                                ('fname', 'VARCHAR(128)'),
                                ('lname', 'VARCHAR(128)'),
                                ('gender', 'VARCHAR(8)'),
                                ('birthday', 'DATE'),
                                ('city', 'VARCHAR(32)'),
                                ('state', 'VARCHAR(32)'),
                                ('updated', 'TIMESTAMP', 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
                            ],
                            key=['fbid'])

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
                            key=['fbid_source', 'fbid_target'])

TABLES['events'] =    Table(name='events',
                            cols=[
                                ('session_id', 'VARCHAR(128)'),
                                ('ip', 'VARCHAR(32)'),
                                ('fbid', 'BIGINT'),
                                ('friend_fbid', 'BIGINT'),
                                ('type', 'VARCHAR(64)'),
                                ('appid', 'BIGINT'),
                                ('content', 'VARCHAR(128)'),
                                ('activity_id', 'BIGINT'),
                                ('updated', 'TIMESTAMP', 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
                            ],
                            indices=['session_id', 'fbid', 'friend_fbid', 'activity_id'])

# Reset the DB by dropping and recreating tables
def dbSetup(connP=None, tableKeys=None):
    conn = connP if (connP is not None) else getConn()
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
    conn.commit()
    if (connP is None):
        conn.close()

def dbMigrate():
    conn = getConn()
    curs = conn.cursor()

    # create the new token table
    dbSetup(conn, tableKeys=["tokens"])

    # rename users table
    curs.execute("RENAME TABLE users TO users_OLD")

    #copy existing tokens from the old users table to the new tokens table
    curs.execute("SELECT fbid, token FROM users_OLD WHERE (token IS NOT NULL)")
    tok_fbid = {}
    for fbid, tok in curs.fetchall():
        token = datastructs.TokenInfo(tok, fbid, config["fb_app_id"], datetime.datetime(2013, 6, 1))
        updateTokensDb(curs, [fbid], token)
        tok_fbid[tok] = fbid
    curs.execute("SELECT fbid, friend_token FROM users_OLD WHERE (friend_token IS NOT NULL)")
    for fbid, tokFriend in curs.fetchall():
        if (tokFriend in tok_fbid):
            owner = tok_fbid[token]
            token = datastructs.TokenInfo(tokFriend, owner, config["fb_app_id"], datetime.datetime(2013, 6, 1))
            updateTokensDb(curs, [fbid], token)

    # create the new users table
    dbSetup(conn, tableKeys=["users"])

    # insert old user rows into new table
    sql = """
        INSERT INTO users (fbid, fname, lname, gender, birthday, city, state)
            SELECT fbid, fname, lname, gender, CASE WHEN birthday='None' THEN NULL ELSE birthday END, city, state
            FROM users_OLD
    """
    curs.execute(sql)

    return




def getUserTokenDb(connP, userId, appId):
    """grab the "best" token from the tokens table

    For now, it simply grabs all non-expired tokens and orders them by
    primary status (whether owner matches user), followed by updated date.
    """
    conn = connP if (connP is not None) else getConn()
    curs = conn.cursor()
    ts = time.time()
    sql = "SELECT token, ownerid, unix_timestamp(expiration) FROM tokens WHERE fbid=%s AND expiration<%s AND appid=%s"
    params = (userId, ts, appId)
    sql += "ORDER BY CASE WHEN userid=ownerid THEN 0 ELSE 1 END, updated DESC"
    curs.execute(sql, params)
    rec = curs.fetchone()
    if (rec is None):
        ret = None
    else:
        expDate = datetime.utcfromtimestamp(rec[2])
        ret = datastructs.TokenInfo(rec[0], rec[1], appId, expDate)
    if (connP is None):
        conn.close()
    return ret


def getUserDb(connP, userId, freshnessDays=36525, freshnessIncludeEdge=False): # 100 years!
    conn = connP if (connP is not None) else getConn()

    freshnessDate = datetime.datetime.now() - datetime.timedelta(days=freshnessDays)
    logging.debug("getting user %s, freshness date is %s" % (userId, freshnessDate.strftime("%Y-%m-%d %H:%M:%S")))
    sql = """SELECT fbid, fname, lname, gender, birthday, city, state, updated FROM users WHERE fbid=%s""" % userId
    #logging.debug(sql)
    curs = conn.cursor()
    curs.execute(sql)
    rec = curs.fetchone()
    if (rec is None):
        ret = None
    else:
        fbid, fname, lname, gender, birthday, city, state, updated = rec
        logging.debug("getting user %s, update date is %s" % (userId, updated.strftime("%Y-%m-%d %H:%M:%S")))

        if (updated <= freshnessDate):
            ret = None
        else:
            if (freshnessIncludeEdge):
                curs.execute("SELECT max(updated) as freshnessEdge FROM edges WHERE prim_id=%s OR sec_id=%s", (userId, userId))
                rec = curs.fetchone()
                updatedEdge = rec[0]
                if (updatedEdge is None) or (datetime.date.fromtimestamp(updatedEdge) < freshnessDate):
                    ret = None
                else:
                    ret = datastructs.UserInfo(fbid, fname, lname, gender, birthday, city, state)
            else:
                ret = datastructs.UserInfo(fbid, fname, lname, gender, birthday, city, state)
    if (connP is None):
        conn.close()
    return ret


def getFriendEdgesDb(connP, primId, requireOutgoing=False, newerThan=0):
    conn = connP if (connP is not None) else getConn()

    edges = []  # list of edges to be returned
    primary = getUserDb(conn, primId)

    curs = conn.cursor()
    sqlSelect = """
            SELECT fbid_source, fbid_target,
                    post_likes, post_comms, stat_likes, stat_comms, wall_posts, wall_comms,
                    tags, photos_target, photos_other, mut_friends, updated
            FROM edges
            WHERE updated>%s
    """

    sql = sqlSelect + " AND fbid_target=%s"
    params = (newerThan, primId)
    secId_edgeCountsIn = {}
    curs.execute(sql, params)
    for rec in curs: # here, the secondary is the source, primary is the target
        secId, primId, iPstLk, iPstCm, iStLk, iStCm, iWaPst, iWaCm, iTags, iPhOwn, iPhOth, iMuts, iUpdated = rec
        edgeCountsIn = datastructs.EdgeCounts(secId, primId,
                                              iPstLk, iPstCm, iStLk, iStCm, iWaPst, iWaCm,
                                              iTags, iPhOwn, iPhOth, iMuts)
        secId_edgeCountsIn[secId] = edgeCountsIn

    if (not requireOutgoing):
        # for pId, sId, inPstLk, inPstCm, inStLk, inStCm, inWaPst, inWaCm, inTags, photPrim, photOth, muts, updated in curs:
        #     secondary = getUserDb(conn, sId)
        #
        #     # edges.append(datastructs.EdgeFromCounts1(primary, secondary,
        #     #                                          inPstLk, inPstCm, inStLk, inStCm, inWaPst, inWaCm, inTags,
        #     #                                          photPrim, photOth, muts))
        #
        #     edgeCountsIn = datastructs.EdgeCounts(secondary, primary,
        #                                           inPstLk, inPstCm, inStLk, inStCm, inWaPst, inWaCm,
        #                                           inTags, photPrim, photOth)
        #
        #     edges.append(datastructs.Edge(primary, secondary, edgeCountsIn, None, muts))
        for secId, edgeCountsIn in secId_edgeCountsIn.items():
            secondary = getUserDb(conn, secId)
            edges.append(datastructs.Edge(primary, secondary, edgeCountsIn, None))

    else:
        # sId_rec1 = dict([ (rec[1], rec) for rec in curs ])  # index should match secId in query above
        sql = sqlSelect + " AND fbid_source=%s"
        params = (newerThan, primId)
        curs.execute(sql, params)
        for rec in curs: # here, primary is the source, secondary is target
            primId, secId, oPstLk, oPstCm, oStLk, oStCm, oWaPst, oWaCm, oTags, oPhOwn, oPhOth, oMuts, oUpdated = rec
            edgeCountsOut = datastructs.EdgeCounts(primId, secId,
                                                   oPstLk, oPstCm, oStLk, oStCm, oWaPst, oWaCm,
                                                   oTags, oPhOwn, oPhOth, oMuts)
            edgeCountsIn = secId_edgeCountsIn[secId]
            secondary = getUserDb(conn, secId)

            #rec1 = sId_rec1[sId]
            #pId, sId, iPstLk, iPstCm, iStLk, iStCm, iWaPst, iWaCm, iTags, iPhPrim, iPhOth, iMuts, iUpdated = rec1

            # e = datastructs.EdgeFromCounts2(primary, secondary,
            #                                 iPstLk, iPstCm, iStLk, iStCm, iWaPst, iWaCm, iTags,
            #                                 oPstLk, oPstCm, oStLk, oStCm, oWaPst, oWaCm, oTags,
            #                                 max(iPhPrim, oPhPrim), max(iPhOth, oPhOth), max(iMuts, oMuts), None)
            # edges.append(e)

            edges.append(datastructs.Edge(primary, secondary, edgeCountsIn, edgeCountsOut))

    if (connP is None):
        conn.close()
    return edges

# helper function that may get run in a background thread
def _updateDb(user, token, edges):
    tim = datastructs.Timer()
    conn = getConn()
    curs = conn.cursor()
    updateUsersDb(curs, [user])
    updateTokensDb(curs, [user], token)
    fCount = updateUsersDb(curs, [e.secondary for e in edges])
    tCount = updateTokensDb(curs, [e.secondary for e in edges], token)
    eCount = updateFriendEdgesDb(curs, edges)
    conn.commit()
    logging.debug("updateFriendEdgesDb() thread %d updated %d friends, %d tokens, %d edges for user %d (took %s)" %
                    (threading.current_thread().ident, fCount, tCount, eCount, user.id, tim.elapsedPr()))
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

def updateFriendEdgesDb(curs, edges):
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
                    'mut_friends': counts.mutuals
                }
                writeCount += upsert(curs, "edges", col_val)

    #
    # incoming = ['in_post_likes', 'in_post_comms', 'in_stat_likes', 'in_stat_comms']
    # outgoing = ['out_post_likes', 'out_post_comms', 'out_stat_likes', 'out_stat_comms']
    #
    # coalesceCols = []
    # overwriteCols = incoming + ['mut_friends', 'updated']
    # if (overwriteOutgoing):
    #     overwriteCols.extend(outgoing)
    # else:
    #     coalesceCols.extend(outgoing)
    #
    # joinCols = ['prim_id', 'sec_id']
    #
    # vals = [{
    #         'prim_id': e.primary.id, 'sec_id': e.secondary.id,
    #         'in_post_likes': e.inPostLikes, 'in_post_comms': e.inPostComms,
    #         'in_stat_likes': e.inStatLikes, 'in_stat_comms': e.inStatComms,
    #         'out_post_likes': e.outPostLikes, 'out_post_comms': e.outPostComms,
    #         'out_stat_likes': e.outStatLikes, 'out_stat_comms': e.outStatComms,
    #         'mut_friends': e.mutuals, 'updated': time.time()
    #         } for e in edges]
    #
    # return db.insert_update(curs, 'edges', coalesceCols, overwriteCols, joinCols, vals)
    return writeCount


def updateUsersDb(curs, users):
    # coalesceCols = []
    # overwriteCols = ['fname', 'lname', 'gender', 'birthday', 'city', 'state', 'updated']
    # joinCols = ['fbid']
    # vals = [{
    #         'fbid': u.id, 'fname': u.fname, 'lname': u.lname, 'gender': u.gender,
    #         'birthday': str(u.birthday), 'city': u.city, 'state': u.state,
    #         'updated': time.time()
    #         } for u in users]
    # return db.insert_update(curs, 'users', coalesceCols, overwriteCols, joinCols, vals)
    updateCount = 0
    for u in users:
        col_val = { 'fbid': u.id, 'fname': u.fname, 'lname': u.lname, 'gender': u.gender, 'birthday': u.birthday,
                    'city': u.city, 'state': u.state, 'updated': None }
        updateCount += upsert(curs, 'users', col_val)
    return updateCount

def updateTokensDb(curs, users, token):
    insertedTokens = 0
    for user in users:
        col_val = {
            'fbid': user.id,
            'appid': token.appId,
            'ownerid': token.ownerId,
            'token':token.tok,
            'expires': token.expires,
            'updated': None
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

    sql = "INSERT INTO " + table + " (" + ", ".join(keyColNames + valColNames) + ") "
    sql += "VALUES (" + ", ".join(keyColWilds + valColWilds) + ") "
    sql += "ON DUPLICATE KEY UPDATE " + ", ".join([ c + "=%s" for c in valColNames])
    params = keyColVals + valColVals + valColVals
    logging.debug("upsert sql: " + sql + " " + str(params))
    curs.execute(sql, params)
    return curs.rowcount

# # keeping this around just in case we want to go back to a two-step process... if we do, we MUST use
# # transactions to avoid race conditions.
# def insert_update(curs, updateTable, coalesceCols, overwriteCols, keyCols, vals):
#     """Helper class to update records in a table."""
#     allCols = keyCols + overwriteCols + coalesceCols
#     keySQL = ' AND '.join([ c + ' = %('+c+')s' for c in keyCols ])
#
#     selectSQL = "SELECT %s FROM %s WHERE %s" % ( ', '.join(keyCols), updateTable, keySQL )
#
#     coalesceSQL  = [ '%s = COALESCE(%s, %s)' % (c, '%('+c+')s', c) for c in coalesceCols ]
#     overwriteSQL = [ '%s = %s' % (c, '%('+c+')s') for c in overwriteCols ]
#     upColsSQL = ', '.join(overwriteSQL + coalesceSQL)
#     updateSQL = "UPDATE %s SET %s WHERE %s" % (updateTable, upColsSQL, keySQL)
#
#     insertSQL = "INSERT INTO %s (%s) VALUES (%s)" % (
#         updateTable, ', '.join(allCols), ', '.join(['%('+c+')s' for c in allCols]) )
#
#     insertCount = 0
#     for row in vals:
#
#         curs.execute(selectSQL, row)
#
#         sql = updateSQL if ( curs.fetchone() ) else insertSQL
#         curs.execute(sql, row)
#
#         curs.execute("COMMIT")
#         insertCount += 1
#
#     return insertCount





# helper function that may get run in a background thread
def _writeEventsDb(sessionId, ip, userId, friendIds, eventType, appId, content, activityId):
    tim = datastructs.Timer()
    conn = getConn()
    curs = conn.cursor()

    rows = [{'sessionId': sessionId, 'ip': ip, 'userId': userId, 'friendId': friendId,
             'eventType': eventType, 'appId': appId, 'content': content,
             'activityId': activityId, 'createDt': time.strftime("%Y-%m-%d %H:%M:%S")
            } for friendId in friendIds]
    sql = """INSERT INTO events (session_id, ip, fbid, friend_fbid, type, appid, content, activity_id, updated)
                VALUES (%(sessionId)s, %(ip)s, %(userId)s, %(friendId)s, %(eventType)s, %(appId)s, %(content)s, %(activityId)s, %(createDt)s) """

    insertCount = 0
    for row in rows:
        curs.execute(sql, row)
        conn.commit()
        insertCount += 1

    logging.debug("_writeEventsDb() thread %d updated %d %s event(s) from session %s" % (threading.current_thread().ident, insertCount, eventType, sessionId))
    conn.close()

    return insertCount

def writeEventsDb(sessionId, ip, userId, friendIds, eventType, appId, content, activityId, background=False):
    # friendIds should be a list (as we may want to write multiple shares or suppressions at the same time)
    if (background):
        t = threading.Thread(target=_writeEventsDb,
                             args=(sessionId, ip, userId, friendIds, eventType, appId, content, activityId))
        t.daemon = False
        t.start()
        logging.debug("writeEventsDb() spawning background thread %d for %s event from session %s" % (
            t.ident, eventType, sessionId))
        return 0
    else:
        logging.debug("writeEventsDb() foreground thread %d for %s event from session %s" % (
            threading.current_thread().ident, eventType, sessionId))
        return _writeEventsDb(sessionId, ip, userId, friendIds, eventType, appId, content, activityId)
