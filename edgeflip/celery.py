from __future__ import absolute_import

from celery import Celery
from edgeflip.settings import config

celery = Celery('edgeflip.celery',
                broker='amqp://%s:%s@%s:5672/%s' % (
                    config.rabbit_user,
                    config.rabbit_pass,
                    config.rabbit_host,
                    config.rabbit_vhost
                ),
                include=['edgeflip.tasks'])

celery.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_RESULT_BACKEND='database',
    CELERY_RESULT_DBURI="mysql://%s:%s@%s/%s" % (
        config.dbuser,
        config.dbpass,
        config.dbhost,
        config.dbname,
    ),
    CELERY_ALWAYS_EAGER=config.always_eager,
    CELERY_ROUTES={
        'edgeflip.tasks.px3_crawl': {'queue': 'px3'},
        'edgeflip.tasks.perform_filtering': {'queue': 'px3_filter'},
        'edgeflip.tasks.proximity_rank_four': {'queue': 'px4'},
    }
)

if __name__ == '__main__':
    celery.start()
