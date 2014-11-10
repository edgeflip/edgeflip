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

    COOKIE_REFERERS_NAME = 'testcookie_referers'

    def process_response(self, request, response):
        try:
            session = request.session
        except AttributeError:
            # Response generated before SessionMiddleware.process_request ran; bail:
            return response

        if session.test_cookie_worked():
            # We set a cookie-testing session value in a previous response,
            # and the user agent has proven it can hold onto session cookies.
            cleanup = getattr(settings, 'SESSION_COOKIE_VERIFICATION_DELETE', True)

            if cleanup:
                session.delete_test_cookie()

            visit = getattr(request, 'visit', None)
            referer = request.META.get('HTTP_REFERER', '')[:1028]

            # If we're not cleaning up the test, rather than lock database rows
            # on every response, we'll first check a (non-isolated and inexact!)
            # record of referrers:
            recorded = session.get(self.COOKIE_REFERERS_NAME, [])

            if visit and settings.SESSION_COOKIE_DOMAIN in referer and (
                cleanup or referer not in recorded
            ):
                # We have no uniqueness constraint to defend against duplicate events
                # created by competing threads, so lock get() via select_for_update
                with transaction.atomic():
                    relational.Event.objects.select_for_update().get_or_create(
                        visit=visit,
                        event_type='cookies_enabled',
                        content=referer,
                    )

                if not cleanup:
                    recorded.append(referer)
                    session[self.COOKIE_REFERERS_NAME] = recorded

        if not request.is_ajax():
            # Don't bother unless it's a new "page" request
            session.set_test_cookie()

        return response


class P3PMiddleware(object):

    def process_response(self, request, response):
        ''' IE10 is a meanie, and remains the only browser to respect P3P
        (http://www.w3.org/P3P/). Without a P3P setting, our cookies will be
        rejected by IE10, and then a lot of our functionality breaks down.

        For now, we have a dummy string in there that IE10 will amazingly
        accept as valid. However, long term we need to handle this via:
            https://trello.com/c/pTyZi1Rh
        '''
        response['P3P'] = 'CP="This is not a privacy policy!"'
        return response
