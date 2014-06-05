from django.db import models

class Campaignstats(models.Model):
    campaign_id = models.PositiveIntegerField()
    visits = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    authorized_visits = models.PositiveIntegerField(default=0)
    uniq_users_authorized = models.PositiveIntegerField(default=0)
    auth_fails = models.PositiveIntegerField(default=0)
    visits_generated_faces = models.PositiveIntegerField(default=0)
    users_generated_faces = models.PositiveIntegerField(default=0)
    visits_facepage_rendered = models.PositiveIntegerField(default=0)
    users_facepage_rendered = models.PositiveIntegerField(default=0)
    visits_shown_faces = models.PositiveIntegerField(default=0)
    users_shown_faces = models.PositiveIntegerField(default=0)
    total_faces_shown = models.PositiveIntegerField(default=0)
    distinct_faces_shown = models.PositiveIntegerField(default=0)
    visits_with_share_clicks = models.PositiveIntegerField(default=0)
    visits_with_shares = models.PositiveIntegerField(default=0)
    users_who_shared = models.PositiveIntegerField(default=0)
    audience = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    clickbacks = models.PositiveIntegerField(default=0)

    class Meta(object):
        app_label = 'reporting'
        db_table = 'campaignstats'
