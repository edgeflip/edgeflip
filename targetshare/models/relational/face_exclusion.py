from django.db import models


class FaceExclusion(models.Model):

    face_exclusion_id = models.AutoField(primary_key=True)
    fbid = models.BigIntegerField()
    campaign = models.ForeignKey('Campaign',
        help_text='Root campaign through which message was shared with friend')
    content = models.ForeignKey('ClientContent')
    friend_fbid = models.BigIntegerField()
    reason = models.CharField(max_length=512, null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        app_label = 'targetshare'
        unique_together = ('fbid', 'campaign', 'content', 'friend_fbid')
        db_table = 'face_exclusions'
