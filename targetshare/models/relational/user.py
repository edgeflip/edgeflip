from django.db import models


class User(models.Model):

    fbid = models.BigIntegerField(primary_key=True)
    first_name = models.CharField(max_length=128, null=True, db_column='fname')
    last_name = models.CharField(max_length=128, null=True, db_column='lname')
    email = models.CharField(max_length=256, null=True)
    gender = models.CharField(max_length=8, null=True)
    birthday = models.DateTimeField(null=True)
    city = models.CharField(max_length=32, null=True)
    state = models.CharField(max_length=32, null=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)

    class Meta:
        db_table = 'users'
