from django.db import models


class ButtonStyle(models.Model):

    button_style_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'button_styles'
