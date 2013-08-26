# Connect signals #
from .base import item_declared as _item_declared
from .utils import database as _database

_item_declared.connect(_database.register_item)


# Make item classes available #
from .user import User
