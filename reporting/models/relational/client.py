from django.db import models


class Client(models.Model):

    client_id = models.IntegerField()
    name = models.CharField(max_length=255, unique=True)
    codename = models.SlugField(unique=True)
    fb_app_name = models.CharField(max_length=256)
    fb_app_id = models.CharField(max_length=256)
    domain = models.CharField(max_length=256)
    subdomain = models.CharField(max_length=256)
    source_parameter = models.CharField(default='rs', max_length=15)
    create_dt = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'reporting'
        db_table = 'clients'
