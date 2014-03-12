from django.http import Http404

from jsurls import utils

handlers = utils.load_from_staticfiles('handlers')
StaticFilesHandler = getattr(handlers, 'StaticFilesHandler', object)


class JsUrlsStaticFilesHandler(StaticFilesHandler):

    @classmethod
    def replacestatic(cls, handler):
        if StaticFilesHandler is not object and isinstance(handler, StaticFilesHandler):
            return cls(handler.application, handler.base_dir)
        return handler

    def get_response(self, request):
        if self._should_handle(request.path):
            try:
                return self.serve(request)
            except Http404:
                pass # Don't 404 eagerly
        return super(StaticFilesHandler, self).get_response(request)
