from decimal import Decimal

from django.db import models

from .base import BaseModel


class FBApp(BaseModel):

    appid = models.BigIntegerField('FB App ID', primary_key=True)
    name = models.CharField('FB App Namespace', max_length=255, unique=True)
    secret = models.CharField('FB App Secret', max_length=32)
    api = models.DecimalField('FB API Version', max_digits=3, decimal_places=1,
                              default=Decimal('2.2'))
    permissions = models.ManyToManyField('targetshare.FBPermission', blank=True)

    class Meta(BaseModel.Meta):
        db_table = 'fb_apps'
        ordering = ('name',)

    def __unicode__(self):
        return self.name
