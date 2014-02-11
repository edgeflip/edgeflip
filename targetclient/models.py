from django.db import models


class OFAToken(models.Model):

    facebook_id = models.CharField(max_length=64, unique=True)
    facebook_access_token = models.CharField(max_length=255)
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True)

    class Meta(object):
        db_table = 'facebook_informations'
