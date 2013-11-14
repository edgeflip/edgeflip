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
        try:
            session = request.session
        except AttributeError:
            # http://stackoverflow.com/questions/11783404/wsgirequest-object-has-no-attribute-session
            return response

        if session.test_cookie_worked():
            session.delete_test_cookie()

            visit = getattr(request, 'visit', None)
            referer = request.META.get('HTTP_REFERER', '')
            if settings.SESSION_COOKIE_DOMAIN in referer and visit:
                # TODO: Block competing thread during transaction
                # DETERMINE: Does select_for_update work if select not expected to return any rows?
                relational.Event.objects.get_or_create(
                    visit=visit,
                    event_type='cookies_enabled',
                    content=referer[:1028],
                )

        if not request.is_ajax():
            # Must be a new request
            session.set_test_cookie()

        return response
