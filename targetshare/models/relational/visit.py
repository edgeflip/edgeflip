from django.db import models


class Visit(models.Model):

    visit_id = models.AutoField(primary_key=True)
    visitor = models.ForeignKey('targetshare.Visitor', related_name='visits')
    session_id = models.CharField(db_index=True, max_length=40)
    app_id = models.BigIntegerField(db_column='appid')
    ip = models.GenericIPAddressField()
    user_agent = models.CharField(blank=True, default='', max_length=1028)
    referer = models.CharField(blank=True, default='', max_length=1028)
    source = models.CharField(blank=True, default='', db_index=True, max_length=256)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'visits'
        unique_together = ('session_id', 'app_id')

    def __unicode__(self):
        return u"{} [{}]".format(self.session_id, self.app_id)
