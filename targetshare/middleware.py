class LazyVisit(object):

    def __init__(self, request, view_func, view_args, view_kwargs):
        self.request = request
        self.view_func = view_func
        self.view_args = view_args
        self.view_kwargs = view_kwargs
        self.cached_visit = None

    def __get__(self, instance, cls=None):
        if self.cached_visit is not None:
            return self.cached_visit
        # ...
        #self.cached_visit = visit
        #return visit


class VisitMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Store lazy object, so as to only process visit if the view wants it
        request.visit = LazyVisit(request, ...)
