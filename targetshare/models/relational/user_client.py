from django.db import models


class UserClient(models.Model):

    user_client_id = models.AutoField(primary_key=True)
    fbid = models.BigIntegerField()
    client = models.ForeignKey('Client')
    create_dt = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        unique_together = ('fbid', 'client')
        db_table = 'user_clients'
