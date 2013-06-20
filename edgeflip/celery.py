from __future__ import absolute_import

from celery import Celery

celery = Celery('edgeflip.celery',
                broker='amqp://edgeflip:edgeflip@localhost:5672/edgehost',
                include=['edgeflip.tasks'])

# Optional configuration, see the application user guide.
celery.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_RESULT_BACKEND='database',
    CELERY_RESULT_DBURI="mysql://root:root@localhost/edgeflip",
    CELERY_ROUTES={
        'edgeflip.tasks.retrieve_fb_user_info': {'queue': 'user_info'},
    }
)

if __name__ == '__main__':
    celery.start()
