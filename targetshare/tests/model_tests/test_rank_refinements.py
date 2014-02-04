from datetime import datetime

from targetshare import models

from .. import EdgeFlipTestCase


class TestRankingKey(EdgeFlipTestCase):

    fixtures = ['test_data']

    @staticmethod
    def make_user(fbid, **kws):
        defaults = {
            'birthday': datetime(1984, 1, 1),
            'fname': 'test',
            'lname': 'user',
            'gender': 'male',
            'city': 'Chicago',
            'state': 'Illinois',
            'country': 'United States'
        }
        return models.dynamo.User(defaults, fbid=fbid, **kws)

    def setUp(self):
        super(TestRankingKey, self).setUp()
        self.client = models.relational.Client.objects.all()[0]
        self.ranking_key = self.client.rankingkeys.create()
        self.key_feature = self.ranking_key.rankingkeyfeatures.create(
            feature='topics[Health]',
            feature_type=models.RankingFeatureType.objects.get_topics(),
            reverse=True,
        )

    def test_retrieve_topics_score(self):
        user = self.make_user(fbid=1)
        user.topics = {'Health': 0.23}
        self.assertEqual(self.key_feature.get_user_value(user), 0.23)

    def test_topics_sort_edges(self):
        edges = [
            models.datastructs.Edge(
                primary=None,
                secondary=self.make_user(fbid=fbid),
                incoming=None,
            )
            for fbid in xrange(1, 7)
        ]
        edges[0].secondary.topics = {}
        edges[1].secondary.topics = {'Health': None}
        edges[2].secondary.topics = None
        edges[3].secondary.topics = {'Health': 0.23}
        edges[4].secondary.topics = {'Health': 0.93}
        edges[5].secondary.topics = {'Health': 0.93}

        edges1 = self.ranking_key.rankingkeyfeatures.sorted_edges(edges)

        self.assertIsNot(edges1, edges)
        fbids = [edge.secondary.fbid for edge in edges1]
        self.assertEqual(fbids, [5, 6, 4, 1, 2, 3])
