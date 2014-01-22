from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils.importlib import import_module

from targetshare import middleware
from targetshare.views import utils
from targetshare.models import relational
from targetshare.tests import EdgeFlipTestCase


class BaseMiddlewareTestCase(EdgeFlipTestCase):

    @classmethod
    def setUpClass(cls):
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

    def setUp(self):
        super(TestCookieVerificationMiddleware, self).setUp()
        self.factory = RequestFactory()
        self.middleware = middleware.CookieVerificationMiddleware()

    def test_initial_visit(self):
        request = self.get_request()
        response = HttpResponse()
        self.assertFalse(request.session.test_cookie_worked())
        self.middleware.process_response(request, response)
        self.assertTrue(request.session.test_cookie_worked())

    def test_second_visit_cookies_work(self):
        request = self.get_request()
        request.session['testcookie'] = 'worked'
        request.session.save()
        request.META['HTTP_REFERER'] = 'test.edgeflip.com'
        utils.set_visit(request, 1)
        self.middleware.process_response(request, HttpResponse())
        self.assertTrue(
            relational.Event.objects.filter(
                event_type='cookies_enabled').exists()
        )

    def test_second_visit_cookies_failed(self):
        request = self.get_request()
        request.META['HTTP_REFERER'] = 'test.edgeflip.com'
        response = HttpResponse()
        utils.set_visit(request, 1)
        self.middleware.process_response(request, response)
        self.assertFalse(
            relational.Event.objects.filter(
                event_type='cookies_enabled').exists()
        )

    def test_no_test_cookie_on_ajax(self):
        request = self.get_request()
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = HttpResponse()
        self.middleware.process_response(request, response)
        assert 'testcookie' not in request.session
