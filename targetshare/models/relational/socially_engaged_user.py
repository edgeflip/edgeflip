from django.db import models


class SociallyEngagedUser(models.Model):

    fbid = models.BigIntegerField(primary_key=True)
    birthday = models.DateField(db_index=True)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    city = models.CharField(max_length=256, db_index=True)
    state = models.CharField(max_length=40, db_index=True)
    gender = models.CharField(max_length=6)
    score = models.FloatField(db_index=True)
    updated = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'socially_engaged_users'
