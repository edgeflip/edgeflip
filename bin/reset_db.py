#!/usr/bin/env python
import edgeflip.database
import edgeflip.client_db_reset as cdbr
edgeflip.database.dbSetup()
cdbr.client_db_reset()
