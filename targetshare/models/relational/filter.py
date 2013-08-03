import logging
import threading
import time

from django.conf import settings
from django.db import models

from targetshare import datastructs, utils


logger = logging.getLogger(__name__)


class Filter(models.Model):

    filter_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=1024, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def _standard_filter(self, user, feature, operator, value):
        if not hasattr(user, feature):
            return False

        user_val = getattr(user, feature)
        user_val = user_val if user_val else ''

        if operator == 'min':
            return user_val >= value

        elif operator == 'max':
            return user_val <= value

        elif operator == 'eq':
            return user_val == value

        elif operator == 'in':
            return user_val in value

    def filter_edges_by_sec(self, edges):
        """Given a list of edge objects, return those objects for which
        the secondary passes the current filter."""
        if not self.filterfeature_set.exists():
            return edges
        for f in self.filterfeature_set.all():
            if f.feature in settings.CIVIS_FILTERS:
                start_time = time.time()
                threads = []
                loopTimeout = 10
                loopSleep = 0.1
                matches = []
                for count, edge in enumerate(edges):
                    t = threading.Thread(
                        target=utils.civis_filter,
                        args=(edge, f.feature, f.operator, f.value, matches)
                    )
                    t.setDaemon(True)
                    t.name = 'civis-%d' % count
                    threads.append(t)
                    t.start()

                timeStop = time.time() + loopTimeout
                while (time.time() < timeStop):
                    threadsAlive = []
                    for t in threads:
                        if t.isAlive():
                            threadsAlive.append(t)

                    threads = threadsAlive
                    if (threadsAlive):
                        time.sleep(loopSleep)
                    else:
                        break
                logger.debug(
                    "Civis matching complete in %s" % (time.time() - start_time)
                )
                edges = [
                    x for x in matches if isinstance(x, datastructs.Edge)
                ]

            # Standard min/max/eq/in filters below
            else:
                edges = [x for x in edges if self._standard_filter(
                    x.secondary, f.feature, f.operator, f.value)]
        return edges

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filters'
