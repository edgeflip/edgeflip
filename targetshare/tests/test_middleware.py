from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils.importlib import import_module

from targetshare import middleware
from targetshare.views import utils
from targetshare.models import relational
from targetshare.tests import EdgeFlipTestCase


class BaseMiddlewareTestCase(EdgeFlipTestCase):

    @classmethod
    def setUpClass(cls):
        super(BaseMiddlewareTestCase, cls).setUpClass()
        cls.session_engine = import_module(settings.SESSION_ENGINE)

    def get_request(self, path='/'):
        cookie = self.factory.cookies.get(settings.SESSION_COOKIE_NAME, None)
        session_key = cookie and cookie.value
        request = self.factory.get(path)
        request.session = self.session_engine.SessionStore(session_key)
        return request


class TestVisitorMiddleware(BaseMiddlewareTestCase):

    def setUp(self):
        super(TestVisitorMiddleware, self).setUp()
        self.factory = RequestFactory()
        self.middleware = middleware.VisitorMiddleware()

    def test_uuid_cookie(self):
        request = self.get_request()
        response = HttpResponse()
        utils.set_visit(request, 1)
        visitor = request.visit.visitor
        response1 = self.middleware.process_response(request, response)
        self.assertEqual(response1, response)
        cookie = response.cookies[settings.VISITOR_COOKIE_NAME]
        self.assertEqual(cookie.value, visitor.uuid)

    def test_no_visit(self):
        response = HttpResponse()
        response1 = self.middleware.process_response(self.get_request(), response)
        self.assertEqual(response1, response)
        self.assertFalse(response.cookies)


@override_settings()
class TestCookieVerificationMiddleware(BaseMiddlewareTestCase):

    def setUp(self):
        super(TestCookieVerificationMiddleware, self).setUp()
        self.factory = RequestFactory()
        self.middleware = middleware.CookieVerificationMiddleware()
        try:
            del settings.SESSION_COOKIE_VERIFICATION_DELETE
        except AttributeError:
            pass

    def test_initial_visit(self):
        request = self.get_request()
        response = HttpResponse()
        self.assertFalse(request.session.test_cookie_worked())
        self.middleware.process_response(request, response)
        self.assertTrue(request.session.test_cookie_worked())

    def test_second_visit_cookies_work(self):
        events = relational.Event.objects.filter(event_type='cookies_enabled')
        self.assertEqual(events.count(), 0)

        request = self.get_request()
        request.META['HTTP_REFERER'] = 'test.edgeflip.com'
        request.session.set_test_cookie()
        utils.set_visit(request, 1)
        self.middleware.process_response(request, HttpResponse())

        self.assertEqual(events.count(), 1)
        self.assertTrue(request.session.test_cookie_worked())
        self.assertNotIn('testcookie_referers', request.session)

    def test_second_visit_cookies_failed(self):
        events = relational.Event.objects.filter(event_type='cookies_enabled')
        self.assertFalse(events.exists())

        request = self.get_request()
        request.META['HTTP_REFERER'] = 'test.edgeflip.com'
        utils.set_visit(request, 1)
        self.middleware.process_response(request, HttpResponse())

        self.assertFalse(events.exists())
        self.assertTrue(request.session.test_cookie_worked())

    def test_no_test_cookie_on_ajax(self):
        events = relational.Event.objects.filter(event_type='cookies_enabled')
        self.assertEqual(events.count(), 0)

        request = self.get_request()
        request.META['HTTP_REFERER'] = 'test.edgeflip.com'
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.session.set_test_cookie()
        utils.set_visit(request, 1)
        self.middleware.process_response(request, HttpResponse())

        self.assertEqual(events.count(), 1)
        self.assertFalse(request.session.test_cookie_worked())
        self.assertNotIn('testcookie', request.session)

    @override_settings(SESSION_COOKIE_VERIFICATION_DELETE=False)
    def test_persistent_result(self):
        events = relational.Event.objects.filter(event_type='cookies_enabled')
        self.assertEqual(events.count(), 0)

        request = self.get_request()
        request.META['HTTP_REFERER'] = 'test.edgeflip.com'
        request.session.set_test_cookie()
        utils.set_visit(request, 1)
        response = HttpResponse()
        self.middleware.process_response(request, response)

        self.assertEqual(events.count(), 1)
        self.assertTrue(request.session.test_cookie_worked())
        self.assertEqual(request.session['testcookie_referers'], ['test.edgeflip.com'])

        self.middleware.process_response(request, response)
        self.assertEqual(events.count(), 1) # referrer already recorded
        self.assertTrue(request.session.test_cookie_worked())

    @override_settings(SESSION_COOKIE_VERIFICATION_DELETE=False)
    def test_persistent_result_ajax(self):
        events = relational.Event.objects.filter(event_type='cookies_enabled')
        self.assertEqual(events.count(), 0)

        request = self.get_request()
        request.META['HTTP_REFERER'] = 'test.edgeflip.com'
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.session.set_test_cookie()
        utils.set_visit(request, 1)
        response = HttpResponse()
        self.middleware.process_response(request, response)

        self.assertEqual(events.count(), 1)
        self.assertTrue(request.session.test_cookie_worked()) # no clean-up
        self.assertEqual(request.session['testcookie_referers'], ['test.edgeflip.com'])

        self.middleware.process_response(request, response)
        self.assertEqual(events.count(), 1) # referrer already recorded
        self.assertTrue(request.session.test_cookie_worked()) # no clean-up


class TestP3PMiddleware(BaseMiddlewareTestCase):

    def setUp(self):
        super(TestP3PMiddleware, self).setUp()
        self.factory = RequestFactory()
        self.middleware = middleware.P3PMiddleware()

    def test_p3p(self):
        request = self.get_request()
        response = HttpResponse()
        self.assertNotIn('P3P', response)
        self.middleware.process_response(request, response)
        self.assertIn('P3P', response)
