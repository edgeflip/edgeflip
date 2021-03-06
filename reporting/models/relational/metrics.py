from django.db import models
class Metrics(models.Model):

    initial_redirects = models.PositiveIntegerField(default=0)
    visits = models.PositiveIntegerField(default=0)
    authorized_visits = models.PositiveIntegerField(default=0)
    uniq_users_authorized = models.PositiveIntegerField(default=0)
    failed_visits = models.PositiveIntegerField(default=0)
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

    class Meta:
        abstract = True
