#!/usr/bin/python
import sys
import ReadStream
import ReadStreamDb

conn = ReadStreamDb.getConn()
userId = sys.argv[1]
tok = sys.argv[2]
outgoing = bool(sys.argv[3])
overwrite = bool(sys.argv[4])

newCount = ReadStream.updateFriendEdgesDb(conn, userId, tok, readFriendStream=outgoing, overwrite=overwrite)






