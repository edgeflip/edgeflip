#!/usr/bin/python
import sys
import os
import time
import ReadStream
import ReadStreamDb

conn = ReadStreamDb.getConn()
userId = sys.argv[1]
tok = sys.argv[2]
outgoing = bool(sys.argv[3])
overwrite = bool(sys.argv[4])

pid = os.getpid()
lockName = "crawl_%s_%d.lock" % (pid, userId)
lock = open(lockName, 'w')
lock.write(time.strftime("%Y%m%d %H:%M:%S"), "\n")
lock.close()
newCount = ReadStream.updateFriendEdgesDb(conn, userId, tok, readFriendStream=outgoing, overwrite=overwrite)
os.unlink(lockName)





