import datetime

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import RequestFactory
from django.utils import timezone
from django.utils.importlib import import_module

from targetshare import models
from targetshare.views.utils import set_visit

from . import EdgeFlipViewTestCase


class TestVisit(EdgeFlipViewTestCase):

    @classmethod
    def setUpClass(cls):
        cls.session_engine = import_module(settings.SESSION_ENGINE)

    def setUp(self):
        super(EdgeFlipViewTestCase, self).setUp()
        self.factory = RequestFactory()

    def get_request(self, path='/'):
        cookie = self.factory.cookies.get(settings.SESSION_COOKIE_NAME, None)
        session_key = cookie and cookie.value
        request = self.factory.get(path)
        request.session = self.session_engine.SessionStore(session_key)
        return request

    def test_new_visit(self):
        request = self.get_request()
        set_visit(request, 1)
        self.assertTrue(request.visit.session_id)
        self.assertEqual(request.visit.app_id, 1)
        start_event = request.visit.events.get()
        self.assertEqual(start_event.event_type, 'session_start')

    def test_update_visit(self):
        request = self.get_request()
        set_visit(request, 1)
        session_id = request.visit.session_id
        self.assertTrue(session_id)
        self.assertIsNone(request.visit.fbid)

        self.factory.cookies[settings.SESSION_COOKIE_NAME] = session_id
        request = self.get_request()
        set_visit(request, 1, fbid=9)
        self.assertEqual(request.visit.session_id, session_id)
        self.assertEqual(request.visit.fbid, 9)

    def test_visit_expiration(self):
        request0 = self.get_request()
        set_visit(request0, 1)
        session_id0 = request0.visit.session_id
        self.assertTrue(session_id0)

        # Make session old:
        session0 = Session.objects.get(session_key=session_id0)
        session0.expire_date = datetime.datetime(1, 1, 1, 0, 0, tzinfo=timezone.utc)
        session0.save()

        self.factory.cookies[settings.SESSION_COOKIE_NAME] = session_id0
        request1 = self.get_request()
        set_visit(request1, 1)
        session_id1 = request1.visit.session_id
        self.assertTrue(session_id1)
        self.assertEqual(session_id1, request1.session.session_key)

        # Play with session to ensure this it's valid:
        request1.session['foo'] = 'bar'
        request1.session.save()
        self.assertEqual(session_id1, request1.session.session_key)
        self.assertEqual(request1.session['foo'], 'bar')

        self.assertNotEqual(request1.visit, request0.visit)
        self.assertNotEqual(session_id1, session_id0)
        self.assertEqual(models.relational.Visit.objects.count(), 2)
