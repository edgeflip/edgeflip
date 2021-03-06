from django.db import models


class UserClient(models.Model):

    user_client_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', related_name='userclients')

    # db_index on fbid should not be necessary b/c fbid is first in unique_together
    # https://dev.mysql.com/doc/refman/5.6/en/multiple-column-indexes.html
    fbid = models.BigIntegerField()

    create_dt = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'user_clients'
        unique_together = ('fbid', 'client')
