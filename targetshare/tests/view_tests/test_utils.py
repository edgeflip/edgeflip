import datetime

from django.conf import settings
from django.contrib.sessions.models import Session
from django.http import QueryDict
from django.test import RequestFactory, TestCase
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from django.utils.importlib import import_module

from targetshare import models
from targetshare.views.utils import faces_url, get_client_ip, get_visitor, set_visit

from .. import EdgeFlipTestCase


class RequestTestCase(EdgeFlipTestCase):

    def setUp(self):
        super(RequestTestCase, self).setUp()
        self.factory = RequestFactory()


class TestGetClientIP(RequestTestCase):

    def test_simple_ip(self):
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='38.88.227.194')
        ip = get_client_ip(request)
        self.assertEqual(ip, '38.88.227.194')

    def test_multiple_ips(self):
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR='38.88.227.194,127.0.0.1')
        ip = get_client_ip(request)
        self.assertEqual(ip, '38.88.227.194')

    def test_partial_null_ips(self):
        request = self.factory.get('/', HTTP_X_FORWARDED_FOR=',127.0.0.1')
        ip = get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')


class TestVisit(RequestTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestVisit, cls).setUpClass()
        cls.session_engine = import_module(settings.SESSION_ENGINE)

    def get_request(self, path='/', data=(), **extra):
        cookie = self.factory.cookies.get(settings.SESSION_COOKIE_NAME, None)
        session_key = cookie and cookie.value
        request = self.factory.get(path, data, **extra)
        request.session = self.session_engine.SessionStore(session_key)
        return request

    def test_new_visit(self):
        request = self.get_request(HTTP_USER_AGENT='testbot',
                                   HTTP_REFERER='http://client.com/foo')
        set_visit(request, 1)
        self.assertTrue(request.visit.session_id)
        self.assertEqual(request.visit.app_id, 1)
        self.assertEqual(request.visit.user_agent, 'testbot')
        self.assertEqual(request.visit.referer, 'http://client.com/foo')
        start_event = request.visit.events.get()
        self.assertEqual(start_event.event_type, 'session_start')

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

    def test_update_visitor_fbid(self):
        request = self.get_request(HTTP_USER_AGENT='testbot',
                                   HTTP_REFERER='http://client.com/foo')
        set_visit(request, 1)
        session_id = request.visit.session_id
        visitor0 = request.visit.visitor
        self.assertTrue(session_id)
        self.assertIsNone(visitor0.fbid)
        self.assertEqual(request.visit.user_agent, 'testbot')
        self.assertEqual(request.visit.referer, 'http://client.com/foo')

        self.factory.cookies[settings.SESSION_COOKIE_NAME] = session_id
        self.factory.cookies[settings.VISITOR_COOKIE_NAME] = visitor0.uuid
        request = self.get_request(HTTP_USER_AGENT='MESSBOT',
                                   HTTP_REFERER='http://client.com/BAR')
        set_visit(request, 1, fbid=9)
        self.assertEqual(request.visit.session_id, session_id)
        self.assertEqual(request.visit.visitor, visitor0)
        self.assertEqual(request.visit.visitor.fbid, 9)
        # user_agent and referrer shouldn't update:
        self.assertEqual(request.visit.user_agent, 'testbot')
        self.assertEqual(request.visit.referer, 'http://client.com/foo')

    def test_swap_visitor(self):
        request = self.get_request()
        set_visit(request, 1)
        session_id = request.visit.session_id
        visitor0 = request.visit.visitor
        self.assertTrue(session_id)

        self.factory.cookies[settings.SESSION_COOKIE_NAME] = session_id
        # Don't persist visitor UUID
        request = self.get_request()
        set_visit(request, 1)
        self.assertEqual(request.visit.session_id, session_id)
        self.assertNotEqual(request.visit.visitor, visitor0)


class TestVisitor(RequestTestCase):

    def test_new_visitor(self):
        self.assertFalse(models.Visitor.objects.exists())

        request = self.factory.get('/')
        visitor = get_visitor(request)

        self.assertEqual(visitor, models.Visitor.objects.get())
        self.assertTrue(visitor.uuid)
        self.assertIsNone(visitor.fbid)

    def test_new_visitor_fbid(self):
        self.assertFalse(models.Visitor.objects.exists())

        request = self.factory.get('/')
        visitor = get_visitor(request, fbid=123)

        self.assertEqual(visitor, models.Visitor.objects.get())
        self.assertTrue(visitor.uuid)
        self.assertEqual(visitor.fbid, 123)

    def test_retrieve_visitor_from_uuid(self):
        visitor = models.Visitor.objects.create()
        self.assertTrue(visitor.uuid)
        self.factory.cookies[settings.VISITOR_COOKIE_NAME] = visitor.uuid
        request = self.factory.get('/')
        visitor1 = get_visitor(request)
        self.assertEqual(visitor1, visitor)
        self.assertEqual(models.Visitor.objects.count(), 1)

    def test_visitor_fbid_trumps_uuid(self):
        visitor = models.Visitor.objects.create()
        visitor1 = models.Visitor.objects.create(fbid=123)
        self.assertTrue(visitor.uuid)
        self.assertTrue(visitor1.uuid)
        self.factory.cookies[settings.VISITOR_COOKIE_NAME] = visitor.uuid

        request = self.factory.get('/')
        visitor2 = get_visitor(request, fbid=123)
        self.assertEqual(visitor2, visitor1)
        self.assertEqual(models.Visitor.objects.count(), 2)

    def test_update_visitor_fbid(self):
        visitor = models.Visitor.objects.create()
        self.assertTrue(visitor.uuid)
        self.assertIsNone(visitor.fbid)
        self.factory.cookies[settings.VISITOR_COOKIE_NAME] = visitor.uuid
        request = self.factory.get('/')
        visitor1 = get_visitor(request, fbid=123)
        self.assertEqual(visitor1, visitor)
        self.assertEqual(models.Visitor.objects.count(), 1)
        self.assertEqual(visitor1.fbid, 123)

    def test_visitor_fbid_conflict(self):
        visitor = models.Visitor.objects.create(fbid=123)
        self.assertTrue(visitor.uuid)
        self.factory.cookies[settings.VISITOR_COOKIE_NAME] = visitor.uuid
        request = self.factory.get('/')
        visitor1 = get_visitor(request, fbid=321)
        self.assertNotEqual(visitor1, visitor)
        self.assertNotEqual(visitor1.uuid, visitor.uuid)
        self.assertEqual(models.Visitor.objects.count(), 2)
        self.assertTrue(visitor1.uuid)
        self.assertEqual(visitor1.fbid, 321)


class TestFacesUrl(TestCase):

    def setUp(self):
        fb_app = models.FBApp.objects.create(appid=1, name='social-good', secret='sekret')
        client = fb_app.clients.create(name='Klient')
        self.campaign = client.campaigns.create(campaign_id=1)

    def test_basic_url(self):
        self.assertEqual(
            faces_url('http://www.demandaction.org/SandovalSB221Share', self.campaign, 1),
            'http://www.demandaction.org/SandovalSB221Share?efcmpgslug=N9_DHXOFmaI'
        )

    def test_url_with_query(self):
        self.assertEqual(
            faces_url('http://www.demandaction.org/SandovalSB221Share?cake=good', self.campaign, 1),
            'http://www.demandaction.org/SandovalSB221Share?cake=good&efcmpgslug=N9_DHXOFmaI'
        )

    def test_basic_url_with_extra(self):
        self.assertEqual(
            faces_url('http://www.demandaction.org/SandovalSB221Share', self.campaign, 1, cake='good'),
            'http://www.demandaction.org/SandovalSB221Share?cake=good&efcmpgslug=N9_DHXOFmaI'
        )

    def test_url_with_extra_query(self):
        self.assertEqual(
            faces_url('http://www.demandaction.org/SandovalSB221Share?cake=good', self.campaign, 1, cookies='great'),
            'http://www.demandaction.org/SandovalSB221Share?cake=good&efcmpgslug=N9_DHXOFmaI&cookies=great'
        )

    def test_url_with_multivalue_extra(self):
        self.assertEqual(
            faces_url('http://www.demandaction.org/SandovalSB221Share?cake=good', self.campaign, 1, MultiValueDict({'churros': ['delicious', 'convenient']}), cookies='great'),
            'http://www.demandaction.org/SandovalSB221Share?cake=good&efcmpgslug=N9_DHXOFmaI&cookies=great&churros=delicious&churros=convenient'
        )

    def test_url_with_querydict_extra(self):
        self.assertEqual(
            faces_url('http://www.demandaction.org/SandovalSB221Share?cake=good', self.campaign, 1, QueryDict('churros=delicious&churros=convenient'), cookies='great'),
            'http://www.demandaction.org/SandovalSB221Share?cake=good&efcmpgslug=N9_DHXOFmaI&cookies=great&churros=delicious&churros=convenient'
        )
