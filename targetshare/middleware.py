from django.conf import settings

from targetshare.tasks import db
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
        if request.session.get('cookies_verified'):
            return response

        referer = request.META.get('HTTP_REFERER')
        visit = getattr(request, 'visit', None)
        if referer and settings.SESSION_COOKIE_DOMAIN in referer:
            if request.session.test_cookie_worked():
                request.session['cookies_verified'] = True
                request.session.save()
                request.session.delete_test_cookie()
                if visit:
                    db.delayed_save(relational.Event(
                        visit=request.visit,
                        event_type='cookies_enabled',
                    ))
            else:
                if visit:
                    db.delayed_save(relational.Event(
                        visit=request.visit,
                        event_type='cookies_failed',
                    ))
        else:
            # Must be a new request
            request.session.set_test_cookie()

        return response
