from django.db import models


class Manager(models.Manager):

    def get_query_set(self):
        return models.query.QuerySet(self.model, using=self._db)
