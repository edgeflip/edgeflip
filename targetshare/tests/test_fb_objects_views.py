import re

from django.core.urlresolvers import reverse
from mock import patch

from targetshare import models

from . import EdgeFlipViewTestCase


@patch.dict('django.conf.settings.WEB', mock_subdomain='testserver')
class TestFBObjectsViews(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    def test_objects_hit_by_fb(self):
        ''' Test hitting the views.object endpoint as the FB crawler '''
        assert not models.Event.objects.exists()
        response = self.client.get(
            reverse('objects', args=[1, 1]),
            HTTP_USER_AGENT='facebookexternalhit'
        )
        self.assertStatusCode(response, 200)
        assert not models.Event.objects.filter(event_type='clickback').exists()
        assert response.context['fb_params']
        assert response.context['content']
        assert response.context['redirect_url']

    def test_objects(self):
        '''Test hitting the views.object endpoint with an activity id as a
        normal, non-fb bot, user

        '''
        self.assertFalse(models.Event.objects.exists())
        response = self.client.get(
            reverse('objects', args=[1, 1]),
            data={'fb_action_ids': 1, 'campaign_id': 1}
        )
        self.assertStatusCode(response, 200)
        self.assertTrue(models.Event.objects.filter(activity_id=1).exists())
        self.assertTrue(response.context['fb_params'])
        self.assertEqual(response.context['fb_params']['fb_object_url'],
                         'https://testserver/objects/1/1/?campaign_id=1&cssslug=')
        redirect_url = '{}?fb_action_ids=1'.format(
            models.ClientContent.objects.get(pk=1).url)
        self.assertEqual(
            response.context['redirect_url'],
            self.get_outgoing_url(redirect_url, 1)
        )
        self.assertTrue(response.context['content'])
        self.assertTrue(
            models.Event.objects.filter(
                event_type='clickback',
                campaign_id=1,
            ).exists()
        )

    def test_objects_source_url(self):
        fb_object = models.FBObject.objects.get(pk=1)
        campaign_fb_object = fb_object.campaignfbobjects.all()[0]
        campaign_fb_object.source_url = 'http://www.google.com/'
        campaign_fb_object.save()
        fb_object.campaignfbobjects.exclude(pk=campaign_fb_object.pk).delete()

        response = self.client.get(
            reverse('objects', args=[1, 1]),
            data={'fb_action_ids': 1, 'campaign_id': 1}
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['fb_params']['fb_object_url'],
                         'https://testserver/objects/1/1/?campaign_id=1&cssslug=')
        self.assertEqual(
            response.context['redirect_url'],
            self.get_outgoing_url('http://www.google.com/?fb_action_ids=1', 1)
        )

    @patch('targetshare.views.fb_objects.LOG')
    def test_objects_ambiguous_source_url(self, log_mock):
        fb_object = models.FBObject.objects.get(pk=1)
        fb_object.campaignfbobjects.create(
            campaign_id=1,
            source_url='http://www.google.com/',
        )
        response = self.client.get(
            reverse('objects', args=[1, 1]),
            data={'fb_action_ids': 1, 'campaign_id': 1}
        )
        self.assertStatusCode(response, 200)
        self.assertTrue(log_mock.exception.called)
        self.assertRegexpMatches(log_mock.exception.mock_calls[0][1][0],
                                 re.compile('ambiguous fbobject source', re.I))
        self.assertEqual(response.context['fb_params']['fb_object_url'],
                         'https://testserver/objects/1/1/?campaign_id=1&cssslug=')
        self.assertGreater(fb_object.campaignfbobjects.count(), 1)
        self.assertEqual(
            response.context['redirect_url'],
            self.get_outgoing_url('http://www.google.com/?fb_action_ids=1', 1)
        )
