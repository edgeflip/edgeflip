from django.db import models


class Client(models.Model):

    client_id = models.IntegerField()
    name = models.CharField(max_length=255, unique=True, blank=True)
    codename = models.SlugField(unique=True, blank=True, editable=False)
    _fb_app_name = models.CharField(
        'FB App Namespace',
        max_length=256,
        db_column='fb_app_name',
        blank=True
    )
    _fb_app_id = models.CharField(
        'FB App ID',
        max_length=256,
        db_column='fb_app_id',
        blank=True
    )
    domain = models.CharField(max_length=256, blank=True)
    subdomain = models.CharField(max_length=256, blank=True)
    source_parameter = models.CharField(
        "Query string key, if any, with which Edgeflip identifies itself "
        "on links outgoing to client",
        blank=True,
        default='rs',
        max_length=15,
    )
    create_dt = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'reporting'
        db_table = 'clients'
