from django.db import models


class RankingKey(models.Model):

    ranking_key_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', related_name='rankingkeys',
                               null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    description = models.CharField(max_length=1024, blank=True)
    # NOTE: Did we end up using refinement_weight (reranked_edges, rescored_edges)?
    refinement_weight = models.FloatField(
        blank=True, default=0.5,
        help_text="A weight with which to apply the ranking key, relative to network proximity, "
                  "to scoring, 0 <= x <= 1.0: 1.0 will re-rank edges entirely by the ranking key, "
                  "with proximity score used only for tie-breaking, and 0 will retain proximity "
                  "ranking, with the ranking key used only for tie-breaking. Default: 0.5."
    )
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'ranking_keys'
        ordering = ('-create_dt',)
