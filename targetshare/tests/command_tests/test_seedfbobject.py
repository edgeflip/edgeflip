import os.path

from django.core.cache import cache
from django.utils import unittest
from mock import Mock, patch

from targetshare.management.commands import seedfbobject
from targetshare.tests import DATA_PATH


GG_FIXTURE = open(os.path.join(DATA_PATH, 'gg.html')).read()


@patch('targetshare.integration.facebook.third_party.requests.get',
       side_effect=(Mock(text=GG_FIXTURE),) * 2)
class TestSeedCache(unittest.TestCase):

    def setUp(self):
        super(TestSeedCache, self).setUp()
        self.command = seedfbobject.Command()

        self.urls = ('http://foo.com/1/', 'http://foo.com/2/')
        for url in self.urls:
            cache.delete('fbobject|{}'.format(url))

    def test_seed_arguments(self, _requests_mock):
        self.command.handle(
            'cache',
            urls=self.urls,
            verbosity=1,
        )

        for url in self.urls:
            meta = cache.get('fbobject|{}'.format(url))
            self.assertEqual(meta['og:title'], "Scholarship for Filipino Midwife Student")
            self.assertEqual(meta['og:description'][:22], "The Philippines, like ")
            self.assertEqual(meta['og:image'],
                "https://dpqe0zkrjo0ak.cloudfront.net/pfil/14426/pict_grid7.jpg")
            self.assertEqual(meta['og:site_name'], "GlobalGiving.org")

    def test_seed_stdin(self, _requests_mock):
        stdin = (url + '\n' for url in self.urls)
        with patch.object(seedfbobject.sys, 'stdin', **{'xreadlines.return_value': stdin}):
            self.command.handle('cache', urls=None, verbosity=1)

        for url in self.urls:
            meta = cache.get('fbobject|{}'.format(url))
            self.assertEqual(meta['og:title'], "Scholarship for Filipino Midwife Student")
            self.assertEqual(meta['og:description'][:22], "The Philippines, like ")
            self.assertEqual(meta['og:image'],
                "https://dpqe0zkrjo0ak.cloudfront.net/pfil/14426/pict_grid7.jpg")
            self.assertEqual(meta['og:site_name'], "GlobalGiving.org")
