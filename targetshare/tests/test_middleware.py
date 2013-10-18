from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils.importlib import import_module

from targetshare import middleware
from targetshare.views import utils


class TestVisitorMiddleware(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.session_engine = import_module(settings.SESSION_ENGINE)

    def setUp(self):
        super(TestVisitorMiddleware, self).setUp()
        self.factory = RequestFactory()
        self.middleware = middleware.VisitorMiddleware()

    def get_request(self, path='/'):
        cookie = self.factory.cookies.get(settings.SESSION_COOKIE_NAME, None)
        session_key = cookie and cookie.value
        request = self.factory.get(path)
        request.session = self.session_engine.SessionStore(session_key)
        return request

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
