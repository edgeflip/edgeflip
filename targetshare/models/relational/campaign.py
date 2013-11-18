from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class Campaign(models.Model):

    campaign_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', null=True, blank=True, related_name='campaigns')
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True, blank=True)

    def global_filter(self, dt=None):
        try:
            return self.campaignglobalfilters.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None

    def choice_set(self, dt=None):
        try:
            return self.campaignchoicesets.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None

    def button_style(self, dt=None):
        try:
            return self.campaignbuttonstyles.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None

    def generic_fb_object(self, dt=None):
        try:
            return self.campaigngenericfbobjects.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None

    def fb_object(self, dt=None):
        try:
            return self.campaignfbobjects.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaigns'
