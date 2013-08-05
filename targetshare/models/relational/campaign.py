from django.db import models


class Campaign(models.Model):

    campaign_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', null=True, blank=True)
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaigns'
