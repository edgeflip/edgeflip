from datetime import datetime
from decimal import Decimal

import mock

from targetshare import models
from targetshare.models.dynamo.base.item import cached_property

from .. import EdgeFlipTestCase


class TestTopics(EdgeFlipTestCase):

    def setUp(self):
        super(TestTopics, self).setUp()
        self.posttopics_set = [
            models.dynamo.PostTopics(
                postid='1_1',
                Health=Decimal('1.0'),
                Sports=Decimal('0.1'),
            ),
            models.dynamo.PostTopics(
                postid='1_2',
                Health=Decimal('0.2'),
                Sports=Decimal('0.5'),
            ),
        ]
        self.user = models.User(
            fbid=1,
            birthday=datetime(1984, 1, 1),
            fname='test',
            lname='user',
            gender='male',
            city='Chicago',
            state='Illinois',
            country='United States'
        )
        self.postinteractions_set = [
            models.dynamo.PostInteractions(
                user=self.user,
                post_topics=self.posttopics_set[0],
                post_likes=1,
                post_comms=2,
                tags=1,
            ),
            models.dynamo.PostInteractions(
                user=self.user,
                post_topics=self.posttopics_set[1],
                post_likes=2,
                post_comms=0,
                tags=1,
            ),
        ]
        for post_interactions in self.postinteractions_set:
            post_interactions.post_topics.save()
            post_interactions.save()

    @staticmethod
    def _interactions_weights(post_interactions):
        interactions_count = sum(post_interactions.document.values())
        for (topic, score) in post_interactions.post_topics.document.items():
            yield (topic, score * interactions_count)

    def test_topics(self):
        naive = {'Health': 0, 'Sports': 0}
        for pi in self.postinteractions_set:
            for (topic, weight) in self._interactions_weights(pi):
                naive[topic] += weight
        topics = {topic: models.dynamo.User._normalize_topic(score)
                  for (topic, score) in naive.items()}
        self.assertEqual(self.user.topics, topics)

    def test_topics_cache(self):
        bad_topics = cached_property(lambda _self: 1 / 0)
        patch = mock.patch.object(models.dynamo.User, 'topics', bad_topics)
        with patch:
            with self.assertRaises(Exception):
                self.user.topics
        self.assertNotIn('topics', vars(self.user))

        topics = self.user.topics
        self.assertTrue(topics)
        self.assertIsInstance(topics, dict)

        with patch:
            topics1 = self.user.topics # No exception
        self.assertIn('topics', vars(self.user))
        self.assertIs(topics1, topics)

    def test_topics_precache(self):
        for post_interactions in self.postinteractions_set:
            post_interactions.delete()
        topics = models.dynamo.User.get_topics(self.postinteractions_set)
        self.assertTrue(topics)
        self.assertFalse(self.user.topics)
        self.user.topics = topics
        self.assertTrue(self.user.topics)
