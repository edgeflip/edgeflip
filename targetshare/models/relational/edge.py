from django.db import models


class Edge(models.Model):

    edge_id = models.AutoField(primary_key=True)
    fbid_source = models.BigIntegerField()
    fbid_target = models.BigIntegerField()
    post_likes = models.IntegerField(null=True)
    post_comms = models.IntegerField(null=True)
    stat_likes = models.IntegerField(null=True)
    stat_comms = models.IntegerField(null=True)
    wall_posts = models.IntegerField(null=True)
    wall_comms = models.IntegerField(null=True)
    tags = models.IntegerField(null=True)
    photos_target = models.IntegerField(null=True)
    photos_other = models.IntegerField(null=True)
    mut_friends = models.IntegerField(null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('fbid_source', 'fbid_target')
        db_table = 'edges'
