from django.db import models

from core.db.models import BaseModel


class EngagedUser(BaseModel):

    fbid = models.BigIntegerField(primary_key=True)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    birthday = models.DateField(db_index=True, null=True)
    city = models.CharField(max_length=256, db_index=True)
    state = models.CharField(max_length=40, db_index=True)
    gender = models.CharField(max_length=6)
    score = models.FloatField(db_index=True)

    class Meta(object):
        db_table = 'engaged_users'
