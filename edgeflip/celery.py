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

# Optional configuration, see the application user guide.
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
        'edgeflip.tasks.retrieve_fb_user_info': {'queue': 'user_info'},
    }
)

if __name__ == '__main__':
    celery.start()
