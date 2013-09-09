# Ensure module is available via simple import:
from . import datastructs

# Make relational model definitions visible to Django:
from .relational import *

# Make dynamo model defintions available for symmetry:
from .dynamo import *
