
from playhouse.sqlite_ext import FTS5Model, SearchField
#
from models.dm_config import db

class PostText(FTS5Model):
    text = SearchField()
    class Meta:
        database = db
        options = {'tokenize': 'porter'}