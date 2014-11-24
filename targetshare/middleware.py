from django.conf import settings


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

    SESSION_VERIFICATION_NAME = 'sessionverified'

    def process_request(self, request):
        try:
            session = request.session
        except AttributeError:
            return None

        if session.test_cookie_worked():
            # We set a cookie-testing session value on a previous request,
            # and the user agent has proven it can hold onto session cookies.

            # Clean up to avoid interference with future tests
            session.delete_test_cookie()

            # Let request handlers know the test passed
            if getattr(settings, 'STORE_SESSION_COOKIE_VERIFICATION', True):
                session[self.SESSION_VERIFICATION_NAME] = True

            # Make a note to record an event on response
            request._session_verification_event = True

        return None

    def process_response(self, request, response):
        try:
            session = request.session
        except AttributeError:
            return response

        try:
            del request._session_verification_event
        except AttributeError:
            pass
        else:
            # We made a note to record an event for the successful test;
            # by now the visit *must* have been set, if it's going to be:
            visit = getattr(request, 'visit', None)
            if visit:
                visit.events.first_or_create(
                    event_type='cookies_enabled',
                    content=request.META.get('HTTP_REFERER', '')[:1028],
                )

        # Initiate the next test
        # (but don't bother unless it's a new "page" request)
        if not request.is_ajax():
            session.set_test_cookie()

        return response


class P3PMiddleware(object):

    def process_response(self, request, response):
        """Insert into the response a fake P3P privacy policy header.

        IE10 is a meanie, and remains the only browser to respect P3P
        (http://www.w3.org/P3P/). Without a P3P setting, our cookies would be
        rejected by IE10, and then a lot of our functionality would break down.

        For now, we have a dummy string in there that IE10 will (amazingly)
        accept as valid. However, long term we may need to handle this
        (via: https://trello.com/c/pTyZi1Rh).

        """
        response['P3P'] = 'CP="This is not a privacy policy!"'
        return response
