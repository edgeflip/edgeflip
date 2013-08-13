#!/usr/bin/env python
import sys
import edgeflip.dynamo
edgeflip.dynamo.create_all_tables()
print>>sys.stderr, "Created all Dynamo tables. This make take several minutes to take effect."
