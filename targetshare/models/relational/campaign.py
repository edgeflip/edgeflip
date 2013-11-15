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

    #FIXME: We *really* need to decide what here could/should be 1 to 1s
    # instead of straight ForeignKeys. We tend to treat items as 1 to 1, but
    # leave open the possibility of many to 1, which leads to weird scenarios
    # like this.
    @property
    def global_filter(self):
        try:
            return self.campaignglobalfilters.get()
        except ObjectDoesNotExist:
            return None

    @property
    def choice_set(self):
        try:
            return self.campaignchoicesets.get()
        except ObjectDoesNotExist:
            return None

    @property
    def button_style(self):
        try:
            return self.campaignbuttonstyles.get()
        except ObjectDoesNotExist:
            return None

    @property
    def generic_fb_object(self):
        try:
            return self.campaigngenericfbobjects.get()
        except ObjectDoesNotExist:
            return None

    @property
    def fb_object(self):
        try:
            return self.campaignfbobjects.get()
        except ObjectDoesNotExist:
            return None

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaigns'
