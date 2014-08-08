from targetshare.tests import EdgeFlipTestCase

from feed_crawler.utils import retryable


class UtilsTestCase(EdgeFlipTestCase):

    def test_retryable_neverworks(self):
        self.iterations = 0

        @retryable(on=(KeyError,), tries=4)
        def do_stuff(arg):
            self.iterations += 1
            d = {'4': '4'}
            return d[arg]

        with self.assertRaises(KeyError):
            do_stuff('1')
        self.assertEquals(self.iterations, 4)

    def test_retryable_eventuallyworks(self):
        self.iterations = 0

        @retryable(on=(KeyError,), tries=4)
        def do_stuff():
            self.iterations += 1
            d = {'3': '3'}
            return d[str(self.iterations)]

        self.assertEquals(do_stuff(), '3')
        self.assertEquals(self.iterations, 3)
