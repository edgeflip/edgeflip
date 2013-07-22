from __future__ import absolute_import
from kombu import Queue

from celery import Celery
from edgeflip.settings import config

QUEUE_ARGS = {'x-ha-policy': 'all'}

celery = Celery('edgeflip.celery',
                broker='amqp://%s:%s@%s:5672/%s' % (
                    config.rabbit_user,
                    config.rabbit_pass,
                    config.rabbit_host,
                    config.rabbit_vhost
                ),
                include=['edgeflip.tasks'])

celery.conf.update(
    BROKER_HEARTBEAT=10,
    BROKER_POOL_LIMIT=0, # ELB makes pooling problematic
    CELERYD_PREFETCH_MULTIPLIER=1,
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_RESULT_BACKEND='database',
    CELERY_RESULT_DBURI="mysql://%s:%s@%s/%s" % (
        config.dbuser,
        config.dbpass,
        config.dbhost,
        config.dbname,
    ),
    # FIXME: Short lived sessions won't be needed once we have more consistent
    # traffic levels. Then MySQL won't kill our connections.
    CELERY_RESULT_DB_SHORT_LIVED_SESSIONS=True,
    CELERY_ALWAYS_EAGER=config.always_eager,
    CELERY_QUEUES=(
        Queue('px3', routing_key='px3.crawl', queue_arguments=QUEUE_ARGS),
        Queue('px3_filter', routing_key='px3.filter', queue_arguments=QUEUE_ARGS),
        Queue('px4', routing_key='px4.crawl', queue_arguments=QUEUE_ARGS),
    ),
    CELERY_ROUTES={
        'edgeflip.tasks.px3_crawl': {
            'queue': 'px3',
            'routing_key': 'px3.crawl'
        },
        'edgeflip.tasks.perform_filtering': {
            'queue': 'px3_filter',
            'routing_key': 'px3.filter'
        },
        'edgeflip.tasks.proximity_rank_four': {
            'queue': 'px4',
            'routing_key': 'px4.crawl'
        },
    }
)

if __name__ == '__main__':
    celery.start()
