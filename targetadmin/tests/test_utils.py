from targetadmin import utils

from targetshare.tests import EdgeFlipTestCase


class TestUtils(EdgeFlipTestCase):

    def test_fix_redirect_url(self):
        for (test_input, expected_output) in (
            ('https://google.com', 'https://google.com'),
            ('google.com', 'https://google.com'),
            ('https://www.google.com', 'https://www.google.com'),
        ):
            self.assertEqual(
                expected_output,
                utils.fix_redirect_url(test_input, 'https')
            )
        self.assertEqual(
            'http://google.com',
            utils.fix_redirect_url('google.com', 'http'),
        )

    def test_fix_image_url(self):
        for (test_input, expected_output) in (
            ('example.com/test.jpeg', 'https://example.com/test.jpeg'),
            ('//example.com/test.jpeg', '//example.com/test.jpeg'),
            ('http://example.com/test.jpeg', 'http://example.com/test.jpeg'),
            ('https://example.com/test.jpeg', 'https://example.com/test.jpeg'),
        ):
            self.assertEqual(
                expected_output,
                utils.fix_image_url(test_input)
            )
