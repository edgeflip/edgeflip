from django.core.urlresolvers import reverse

from targetshare.tests import EdgeFlipTestCase


class TargetMockTest(EdgeFlipTestCase):

    def test_ofa_landing_no_state(self):
        ''' Test views.ofa_landing without a state specified '''
        response = self.client.get(reverse('ofa-landing'))
        self.assertStatusCode(response, 404)

    def test_ofa_landing_bad_state(self):
        ''' Test views.ofa_landing with a bad state '''
        response = self.client.get(reverse('ofa-landing'))
        self.assertStatusCode(response, 404)

    def test_ofa_landing(self):
        ''' Test proper response from views.ofa_landing '''
        response = self.client.get(reverse('ofa-landing'), {
            'state': 'MA'
        })
        self.assertStatusCode(response, 200)
        context = response.context
        self.assertEqual(context['sen_info']['phone'], '617-867-5309')
        self.assertEqual(
            context['page_title'],
            "Tell Sen. Kermit The Frog We're Putting Denial on Trial!"
        )
