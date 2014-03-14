from __future__ import absolute_import

from django.core.management.commands.runserver import Command as RunserverCommand

from jsurls import utils
from jsurls.handlers import JsUrlsStaticFilesHandler


runserver = utils.load_from_staticfiles('management.commands.runserver')
StaticFilesRunserverCommand = getattr(runserver, 'Command', None)


class Command(StaticFilesRunserverCommand or RunserverCommand):

    def get_handler(self, *args, **options):
        handler = super(Command, self).get_handler(*args, **options)
        return JsUrlsStaticFilesHandler.replacestatic(handler)
