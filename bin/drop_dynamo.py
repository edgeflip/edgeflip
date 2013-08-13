#!/usr/bin/env python
import sys
import edgeflip.dynamo
edgeflip.dynamo.drop_all_tables()
print>>sys.stderr, "Dropped all Dynamo tables. This make take several minutes to take effect."
