from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory
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


class TestCookieVerificationMiddleware(BaseMiddlewareTestCase):

    events = relational.Event.objects.filter(event_type='cookies_enabled')

    def setUp(self):
        super(TestCookieVerificationMiddleware, self).setUp()
        self.factory = RequestFactory()
        self.middleware = middleware.CookieVerificationMiddleware()

    def test_initial_visit(self):
        request = self.get_request()
        self.assertNotIn('testcookie', request.session)
        self.assertNotIn('sessionverified', request.session)

        self.middleware.process_request(request)
        self.assertNotIn('sessionverified', request.session)
        self.assertNotIn('testcookie', request.session)

        self.middleware.process_response(request, HttpResponse())
        self.assertNotIn('sessionverified', request.session)
        self.assertEqual(request.session.get('testcookie'), 'worked')

    def test_second_visit_cookies_work(self):
        self.assertEqual(self.events.count(), 0)

        request = self.get_request()
        request.META['HTTP_REFERER'] = 'https://test.edgeflip.com/'
        request.session.set_test_cookie()
        utils.set_visit(request, 1)

        self.middleware.process_request(request)
        self.assertTrue(request.session.get('sessionverified'))
        self.assertNotIn('testcookie', request.session)

        self.middleware.process_response(request, HttpResponse())
        self.assertEqual(self.events.count(), 1)
        self.assertTrue(request.session.get('sessionverified'))
        self.assertEqual(request.session.get('testcookie'), 'worked')

    def test_second_visit_cookies_failed(self):
        self.assertFalse(self.events.exists())

        request = self.get_request()
        request.META['HTTP_REFERER'] = 'https://test.edgeflip.com/'
        utils.set_visit(request, 1)

        self.middleware.process_request(request)
        self.assertNotIn('testcookie', request.session)
        self.assertNotIn('sessionverified', request.session)

        self.middleware.process_response(request, HttpResponse())
        self.assertFalse(self.events.exists())
        self.assertEqual(request.session.get('testcookie'), 'worked')
        self.assertNotIn('sessionverified', request.session)

    def test_no_test_cookie_on_ajax(self):
        self.assertEqual(self.events.count(), 0)

        request = self.get_request()
        request.META['HTTP_REFERER'] = 'https://test.edgeflip.com/'
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.session.set_test_cookie()
        utils.set_visit(request, 1)

        self.middleware.process_request(request)
        self.assertNotIn('testcookie', request.session)
        self.assertTrue(request.session.get('sessionverified'))

        self.middleware.process_response(request, HttpResponse())
        self.assertEqual(self.events.count(), 1)
        self.assertNotIn('testcookie', request.session)
        self.assertTrue(request.session.get('sessionverified'))


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
