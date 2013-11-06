from django.conf import settings

from targetshare.models import relational


class VisitorMiddleware(object):

    def process_response(self, request, response):
        """Set a very long cookie for the Visitor UUID (if one has been generated
        for the request).

        """
        visit = getattr(request, 'visit', None)
        if visit:
            response.set_cookie(
                key=settings.VISITOR_COOKIE_NAME,
                value=visit.visitor.uuid,
                max_age=(60 * 60 * 24 * 365 * 15), # 15 years in seconds
                domain=settings.VISITOR_COOKIE_DOMAIN,
            )
        return response


class CookieVerificationMiddleware(object):

    def process_response(self, request, response):
        # http://stackoverflow.com/questions/11783404/wsgirequest-object-has-no-attribute-session
        if not hasattr(request, 'session'):
            return response

        referer = request.META.get('HTTP_REFERER')
        visit = getattr(request, 'visit', None)
        if referer and settings.SESSION_COOKIE_DOMAIN in referer:
            if request.session.test_cookie_worked() and visit:
                request.session.delete_test_cookie()
                relational.Event.objects.get_or_create(
                    visit=request.visit,
                    event_type='cookies_enabled',
                    content=referer[:1028],
                )

        if not request.is_ajax():
            # Must be a new request
            request.session.set_test_cookie()

        return response
