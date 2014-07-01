from decimal import Decimal

from mock import patch

from targetshare.models.dynamo import PostTopics

from .. import EdgeFlipTestCase


def patch_classify(**values):
    return patch('targetshare.models.dynamo.post_topics.classify', return_value=values)


class TestClassify(EdgeFlipTestCase):

    def _testTopics(self, **scores):
        post_topics = PostTopics.classify('123', 'Words. Words. Wrods.', *scores.keys())
        post_topics.save()
        self.assertEqual(post_topics.pk, ('123', PostTopics.QD_CLASSIFIER))
        self.assertEqual(post_topics.document, scores)

    @patch_classify(cartoons=0.5, cereal=1.0)
    def test(self, _classify_mock):
        """PostTopics.classify() stores classification result"""
        self._testTopics(cartoons=Decimal(0.5), cereal=Decimal(1.0))

    @patch_classify(cartoons=0.31, cereal=0.295167235301)
    def test_inexact_float(self, _classify_mock):
        """PostTopics.classify() stores inexact floats"""
        self._testTopics(cartoons=Decimal('0.31'), cereal=Decimal('0.295167235301'))
