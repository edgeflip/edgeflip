from django.conf import settings
from django.db import transaction

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
        try:
            session = request.session
        except AttributeError:
            return response

        if session.test_cookie_worked():
            session.delete_test_cookie()

            visit = getattr(request, 'visit', None)
            referer = request.META.get('HTTP_REFERER', '')
            if settings.SESSION_COOKIE_DOMAIN in referer and visit:
                # We have no uniqueness constraint to defend against duplicate
                # events created by competing threads, so lock get() via
                # select_for_update:
                with transaction.commit_on_success():
                    relational.Event.objects.select_for_update().get_or_create(
                        visit=visit,
                        event_type='cookies_enabled',
                        content=referer[:1028],
                    )

        if not request.is_ajax():
            # Don't bother unless it's a new "page" request
            session.set_test_cookie()

        return response
