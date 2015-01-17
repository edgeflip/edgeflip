import random
import types

from django.utils import timezone
from freezegun import freeze_time
from mock import patch

from targetshare import models
from targetshare.tasks import targeting
from targetshare.integration import facebook

from .. import EdgeFlipTestCase, patch_facebook


DB_MIN_FRIEND_COUNT = targeting.DB_MIN_FRIEND_COUNT


def classify_fake(corpus, *topics):
    """Fake classifier that will serially classify a corpus as weight 0 or 1."""
    topic = topics[0] if topics else 'classifiers'
    weight = classify_fake.switch
    classify_fake.switch ^= 1
    return {topic: weight}

classify_fake.switch = 0


class TargetingTestCase(EdgeFlipTestCase):

    def setUp(self):
        super(TargetingTestCase, self).setUp()
        self.token = models.datastructs.ShortToken(fbid=1, appid='1', token='1Z')


## PX3-only tests ##

class TestProximityRankThree(TargetingTestCase):

    def setUp(self):
        super(TestProximityRankThree, self).setUp()

        # Set up new campaign:
        app = models.FBApp.objects.create(appid=1, name='Share!', secret='sekret')
        self.client = app.clients.create()
        self.campaign = self.client.campaigns.create()
        self.content = self.client.clientcontent.create()
        self.properties = self.campaign.campaignproperties.create(client_content=self.content)

        # ...and default (no-op) filtering:
        self.default_filter = self.client.filters.create()
        self.choice_set = self.client.choicesets.create()
        self.campaign.campaignglobalfilters.create(filter=self.default_filter, rand_cdf=1)
        self.default_filter.choicesetfilters.create(choice_set=self.choice_set, url_slug='test')
        self.campaign.campaignchoicesets.create(rand_cdf=1, choice_set=self.choice_set)

    @patch_facebook
    def test_proximity_rank_three(self):
        visitor = models.relational.Visitor.objects.create()
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')
        (
            edges_ranked,
            edges_filtered,
            filter_id,
            cs_slug,
            campaign_id,
            content_id,
        ) = targeting.proximity_rank_three(
            self.token,
            visit_id=visit.pk,
            campaign_id=self.campaign.pk,
            content_id=self.content.pk,
            num_faces=5
        )

        # since we perform filtering too, assert that the output looks filtered
        self.assertTrue(edges_ranked)
        self.assertEqual({type(edge) for edge in edges_ranked},
                         {models.datastructs.Edge})
        self.assertIsInstance(edges_filtered, models.datastructs.TieredEdges)
        self.assertEqual({type(edge) for edge in edges_filtered.edges},
                         {models.datastructs.Edge})
        self.assertIsInstance(filter_id, long)
        self.assertIsInstance(cs_slug, (types.NoneType, basestring))

        events = visit.events.all()
        self.assertEqual(events.filter(event_type='px3_started').count(), 1)
        self.assertEqual(events.filter(event_type='px3_completed').count(), 1)

    @patch_facebook
    def test_px3_crawl(self):
        ''' Run the px3_crawl celery task without throwing it
        through the celery/rabbitmq stack, because we're testing our code,
        not celerys.

        Pass in True for mock mode, a dummy FB id, and a dummy token. Should
        get back a lengthy list of Edges.
        '''
        ranked_edges = targeting.px3_crawl(self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)

    @patch('targetshare.tasks.targeting.facebook')
    def test_proximity_rank_three_fail(self, fb_mock):
        ''' Test that asserts we create a px3_failed event when px3 fails '''
        # 4 exceptions: 3 retries, 1 initial call
        fb_mock.client.get_user.side_effect = [IOError, IOError, IOError, IOError]
        visitor = models.relational.Visitor.objects.create()
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')
        with self.assertRaises(IOError):
            targeting.proximity_rank_three.delay(
                self.token,
                visit_id=visit.pk,
                campaign_id=self.campaign.pk,
                content_id=self.content.pk,
            )
        self.assertEqual(
            models.relational.Event.objects.filter(
                visit=visit, event_type='px3_failed').count(),
            1
        )


@freeze_time('2013-01-01')
class TestFiltering(TargetingTestCase):

    fixtures = ['test_data']

    @patch_facebook
    def test_perform_filtering(self):
        ''' Runs the filtering celery task '''
        visitor = models.relational.Visitor.objects.create()
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')
        ranked_edges = targeting.px3_crawl(self.token)
        # Ensure at least one edge passes filter:
        # (NOTE: May have to fiddle with campaign properties as well.)
        ranked_edges[0].secondary.state = 'Illinois'
        (
            edges_ranked,
            edges_filtered,
            filter_id,
            cs_slug,
            campaign_id,
            content_id,
        ) = targeting.perform_filtering(
            ranked_edges,
            campaign_id=1,
            content_id=1,
            fbid=1,
            visit_id=visit.pk,
            num_faces=1,
        )
        self.assertTrue(edges_ranked)
        self.assertEqual({type(edge) for edge in edges_ranked},
                         {models.datastructs.Edge})
        self.assertIsInstance(edges_filtered, models.datastructs.TieredEdges)
        self.assertEqual({type(edge) for edge in edges_filtered.edges},
                         {models.datastructs.Edge})
        self.assertIsInstance(filter_id, long)
        self.assertIsInstance(cs_slug, (types.NoneType, basestring))

    def test_fallback_cascade(self):
        # Some test users and edges
        test_user1 = models.User(
            fbid=1,
            fname='Test',
            lname='User',
            email='test@example.com',
            gender='male',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
            city='Chicago',
            state='Illinois'
        )
        test_user2 = models.User(
            fbid=2,
            fname='Test',
            lname='User',
            email='test@example.com',
            gender='male',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
            city='Toledo',
            state='Ohio'
        )
        test_edge1 = models.datastructs.UserNetwork.Edge(test_user1, test_user1, None, px3_score=0.5)
        test_edge2 = models.datastructs.UserNetwork.Edge(test_user1, test_user2, None, px3_score=0.4)
        visitor = models.relational.Visitor.objects.create(fbid=1)
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')

        ranked_edges = [test_edge2, test_edge1]
        edges_ranked, edges_filtered, filter_id, cs_slug, campaign_id, content_id = targeting.perform_filtering(
            ranked_edges,
            campaign_id=5,
            content_id=1,
            fbid=1,
            visit_id=visit.pk,
            num_faces=10,
        )

        self.assertEquals(edges_filtered.secondary_ids, (1, 2))
        self.assertEquals(edges_filtered[0]['campaign_id'], 5)
        self.assertEquals(edges_filtered[1]['campaign_id'], 6)


## PX4 tests ##

class Px4TargetingTestCase(TargetingTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(Px4TargetingTestCase, self).setUp()

        # Set up new campaign:
        app = models.FBApp.objects.create(appid=1, name='Share!', secret='sekret')
        self.client = app.clients.create()
        self.campaign = self.client.campaigns.create()
        self.content = self.client.clientcontent.create()
        self.properties = self.campaign.campaignproperties.create(client_content=self.content)

        # ...and default (no-op) filtering:
        self.default_filter = models.relational.Filter.objects.get(name='edgeflip default')
        self.choice_set = self.client.choicesets.create()
        self.default_filter.choicesetfilters.create(choice_set=self.choice_set, url_slug='test')
        self.campaign.campaignchoicesets.create(rand_cdf=1, choice_set=self.choice_set)
        visitor = models.relational.Visitor.objects.create()
        self.visit = visitor.visits.create(
            session_id='123456', app_id=123, ip='127.0.0.1')


class TestProximityRankFour(Px4TargetingTestCase):

    @patch_facebook(min_friends=101, max_friends=120)
    @patch('targetshare.tasks.targeting.LOG')
    def test_proximity_rank_four_from_fb(self, logger_mock):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan())

        result = targeting.proximity_rank_four(self.token, campaign_id=self.campaign.pk,
                                               content_id=None, visit_id=self.visit.pk,
                                               num_faces=None)
        ranked_edges = result[0]
        self.assertIsInstance(ranked_edges, models.datastructs.UserNetwork)
        events = self.visit.events.all()
        self.assertEqual(events.filter(event_type='px4_started').count(), 1)
        self.assertEqual(events.filter(event_type='px4_completed').count(), 1)

        interactions_set = tuple(ranked_edges.iter_interactions())
        self.assertTrue(interactions_set)
        assert all(isinstance(i, models.PostInteractions) for i in interactions_set)

        self.assertEqual({type(edge) for edge in ranked_edges},
                         {models.datastructs.Edge})

        assert all(x.incoming.post_likes is not None for x in ranked_edges)
        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))

        self.assertIn('falling back to FB', logger_mock.info.call_args[0][0])
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertGreater(facebook.client.urllib2.urlopen.call_count, 2)

    @patch('targetshare.tasks.targeting.DB_FRIEND_THRESHOLD', new=90)
    @patch('targetshare.tasks.targeting.DB_MIN_FRIEND_COUNT', new=100)
    @patch_facebook(min_friends=1, max_friends=99)
    @patch('targetshare.tasks.targeting.LOG')
    def test_proximity_rank_four_less_than_100_friends(self, logger_mock):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan())

        result = targeting.proximity_rank_four(self.token, campaign_id=self.campaign.pk,
                                             content_id=None, visit_id=self.visit.pk,
                                             num_faces=None)
        ranked_edges = result[0]
        self.assertIsInstance(ranked_edges, models.datastructs.UserNetwork)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)
        events = self.visit.events.all()
        self.assertEqual(events.filter(event_type='px4_started').count(), 1)
        self.assertEqual(events.filter(event_type='px4_completed').count(), 1)

        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))
        self.assertIn(
            'Has %r friends, hitting FB',
            logger_mock.info.call_args[0][0]
        )
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertGreater(facebook.client.urllib2.urlopen.call_count, 2)

    @patch_facebook(min_friends=DB_MIN_FRIEND_COUNT, max_friends=DB_MIN_FRIEND_COUNT)
    @patch('targetshare.tasks.targeting.LOG')
    def test_proximity_rank_four_uses_dynamo(self, logger_mock):
        self.assertEqual(models.dynamo.IncomingEdge.items.count(), 0)
        for x in xrange(2, DB_MIN_FRIEND_COUNT + 2):
            models.User.items.create(fbid=x)
            models.IncomingEdge.items.create(fbid_source=x, fbid_target=1, post_likes=(x % 20))

        result = targeting.proximity_rank_four(
            self.token,
            campaign_id=self.campaign.pk,
            visit_id=self.visit.pk,
            content_id=None,
            num_faces=None,
        )

        ranked_edges = result[0]
        self.assertIsInstance(ranked_edges, models.datastructs.UserNetwork)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)

        events = self.visit.events.all()
        self.assertEqual(events.filter(event_type='px4_started').count(), 1)
        self.assertEqual(events.filter(event_type='px4_completed').count(), 1)

        self.assertGreater(models.dynamo.IncomingEdge.items.count(), 0)

        self.assertIn('using Dynamo data.', logger_mock.info.call_args[0][0])
        # One call to get the user, the other to get the friend count
        self.assertEqual(facebook.client.urllib2.urlopen.call_count, 2)

    @patch('targetshare.tasks.targeting.facebook')
    def test_proximity_rank_four_failure(self, fb_mock):
        """px4 failure records px4_failed event"""
        # 4 exceptions: 3 retries, 1 initial call
        fb_mock.client.get_user.side_effect = [IOError] * 4
        with self.assertRaises(IOError):
            targeting.proximity_rank_four.delay(
                self.token,
                campaign_id=self.campaign.pk,
                content_id=None,
                visit_id=self.visit.pk,
                num_faces=None
            )
        events = self.visit.events.filter(event_type='px4_failed')
        self.assertEqual(events.count(), 1)


class TestFilteringProximityRankFour(Px4TargetingTestCase):

    @patch_facebook(min_friends=15, max_friends=30)
    @patch('targetshare.models.dynamo.post_topics.classify', side_effect=classify_fake)
    def test_px4_filtering(self, classifier_mock):
        """px4 can filter by topic-interest"""
        (stream, ranked_edges) = targeting.px4_crawl(self.token)
        self.assertTrue(stream)
        # Ensure "closest" friend has low ranking:
        ranked_edges[0].interactions.clear()

        # Configure ranking key:
        ranking_key = self.client.rankingkeys.create()
        ranking_key.campaignrankingkeys.create(campaign=self.campaign)
        ranking_key.rankingkeyfeatures.create(
            feature='topics[Weather]',
            feature_type=models.relational.RankingFeatureType.objects.get_topics(),
            reverse=True,
        )

        # Prevent TooFewFriendsError
        self.campaign.campaignproperties.update(min_friends=1)

        # Configure filter:
        client_filter = self.client.filters.create()
        client_filter.filterfeatures.create(
            feature_type=models.relational.FilterFeatureType.objects.get_topics(),
            feature='topics[Weather]',
            operator=models.FilterFeature.Operator.MIN,
            value=0.1,
        )
        self.campaign.campaignglobalfilters.create(filter=client_filter, rand_cdf=1)

        self.assertEqual(models.dynamo.PostTopics.items.count(), 0)

        visitor = models.relational.Visitor.objects.create(fbid=self.token.fbid)
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')

        filtering_result = targeting.px4_filter(
            stream,
            ranked_edges,
            fbid=self.token.fbid,
            campaign_id=self.campaign.pk,
            content_id=self.content.pk,
            visit_id=visit.pk,
            num_faces=1,
        )
        result = targeting.px4_rank(filtering_result)

        self.assertTrue(all(result))
        self.assertTrue(classifier_mock.called)

        self.assertNotEqual(result.ranked, ranked_edges)

        self.assertLess(len(result.filtered), len(result.ranked))
        mismatch = [user for user in result.filtered.secondaries
                    if user.topics['Weather'] < 0.1]
        self.assertFalse(mismatch)

        self.assertGreater(ranked_edges[0].score, ranked_edges[14].score)
        self.assertNotEqual(result.ranked[0].secondary, ranked_edges[0].secondary)
        self.assertGreater(result.ranked[0].secondary.topics['Weather'],
                           result.ranked[14].secondary.topics.get('Weather', 0))
        self.assertGreater(result.filtered.secondaries[0].topics['Weather'],
                           result.filtered.secondaries[-1].topics['Weather'])

        self.assertGreater(models.dynamo.PostTopics.items.count(), 0)

    @patch_facebook(min_friends=DB_MIN_FRIEND_COUNT, max_friends=DB_MIN_FRIEND_COUNT)
    @patch('targetshare.models.dynamo.post_topics.classify')
    def test_px4_filtering_dynamo(self, classifier_mock):
        """px4 can filter by topic-interest, read from DDB"""
        # Set up data in DynamoDB:
        self.assertEqual(models.dynamo.IncomingEdge.items.count(), 0)
        self.assertEqual(models.dynamo.PostTopics.items.count(), 0)
        self.assertEqual(models.dynamo.PostInteractions.items.count(), 0)

        postids = set()
        for fbid in xrange(2, DB_MIN_FRIEND_COUNT + 2):
            models.User.items.create(fbid=fbid)

            post_likes = random.randint(0, 20)
            models.IncomingEdge.items.create(
                fbid_source=fbid,
                fbid_target=1,
                post_likes=post_likes,
            )
            interacted_posts = map(str, random.sample(xrange(1, 21), post_likes))
            postids.update(interacted_posts)
            if interacted_posts: # batch_get_through doesn't like empty set field (#11)
                models.PostInteractionsSet.items.create(
                    fbid=fbid,
                    postids=interacted_posts,
                )
            for postid in interacted_posts:
                models.PostInteractions.items.create(fbid=fbid, postid=postid, post_likes=1)

        self.assertTrue(postids)
        for (count, postid) in enumerate(postids):
            if count == 0:
                # Skip one to test missing post classifications
                continue

            topics = classify_fake("Words, words, words.", 'Weather')
            models.PostTopics.items.create(
                postid=postid,
                classifier=models.PostTopics.QD_CLASSIFIER,
                **topics
            )

        (stream, ranked_edges) = targeting.px4_crawl(self.token)
        self.assertIsNone(stream) # No FB stream

        # Ensure "closest" friend has low ranking:
        ranked_edges[0].interactions.clear()

        # Configure ranking key:
        ranking_key = self.client.rankingkeys.create()
        ranking_key.campaignrankingkeys.create(campaign=self.campaign)
        ranking_key.rankingkeyfeatures.create(
            feature='topics[Weather]',
            feature_type=models.relational.RankingFeatureType.objects.get_topics(),
            reverse=True,
        )

        # Prevent TooFewFriendsError
        self.campaign.campaignproperties.update(min_friends=1)

        # Configure filter:
        client_filter = self.client.filters.create()
        client_filter.filterfeatures.create(
            feature_type=models.relational.FilterFeatureType.objects.get_topics(),
            feature='topics[Weather]',
            operator=models.FilterFeature.Operator.MIN,
            value=0.1,
        )
        self.campaign.campaignglobalfilters.create(filter=client_filter, rand_cdf=1)

        visitor = models.relational.Visitor.objects.create(fbid=self.token.fbid)
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')

        filtering_result = targeting.px4_filter(
            stream,
            ranked_edges,
            fbid=self.token.fbid,
            campaign_id=self.campaign.pk,
            content_id=self.content.pk,
            visit_id=visit.pk,
            num_faces=1,
        )
        result = targeting.px4_rank(filtering_result)

        self.assertTrue(all(result))
        self.assertFalse(classifier_mock.called)

        self.assertNotEqual(result.ranked, ranked_edges)

        self.assertLess(len(result.filtered), len(result.ranked))
        mismatch = [user for user in result.filtered.secondaries
                    if user.topics['Weather'] < 0.1]
        self.assertFalse(mismatch)

        self.assertGreater(ranked_edges[0].score, ranked_edges[-1].score)
        self.assertNotEqual(result.ranked[0].secondary, ranked_edges[0].secondary)
        self.assertGreater(result.ranked[0].secondary.topics['Weather'],
                           result.ranked[-1].secondary.topics.get('Weather', 0))
        self.assertGreater(result.filtered.secondaries[0].topics['Weather'],
                           result.filtered.secondaries[-1].topics['Weather'])


class TestPx4OnlyFilterTargeting(TargetingTestCase):

    def setUp(self):
        super(TestPx4OnlyFilterTargeting, self).setUp()

        # Set up new campaign:
        app = models.FBApp.objects.create(appid=1, name='Share!', secret='sekret')
        self.client = app.clients.create()
        self.campaign = self.client.campaigns.create()
        self.content = self.client.clientcontent.create()
        self.properties = self.campaign.campaignproperties.create(client_content=self.content)

        # ...and default (no-op) filtering:
        self.default_filter = self.client.filters.create()

        # ...and topics filter feature type
        models.FilterFeatureType.objects.create(
            name="Topics", code='topics', px_rank=4, sort_order=6)

        visitor = models.relational.Visitor.objects.create()
        self.visit = visitor.visits.create(session_id='123456', app_id=123, ip='127.0.0.1')

    @patch_facebook(min_friends=20, max_friends=30)
    @patch('targetshare.models.dynamo.post_topics.classify', side_effect=classify_fake)
    def test_px4_global_filter(self, classifier_mock):
        # Configure global filter:
        global_filter = self.client.filters.create()
        global_filter.filterfeatures.create(
            feature_type=models.relational.FilterFeatureType.objects.get_topics(),
            feature='topics[Weather]',
            operator=models.FilterFeature.Operator.MIN,
            value=0.1,
        )
        self.campaign.campaignglobalfilters.create(filter=global_filter, rand_cdf=1)

        # Configure null choiceset:
        choice_set = self.client.choicesets.create()
        choice_set.choicesetfilters.create(filter=self.default_filter)
        self.campaign.campaignchoicesets.create(choice_set=choice_set, rand_cdf=1)

        # px3
        ranked_edges = targeting.px3_crawl(self.token)
        result = targeting.perform_filtering(
            ranked_edges,
            fbid=self.token.fbid,
            campaign_id=self.campaign.pk,
            content_id=self.content.pk,
            visit_id=self.visit.pk,
            num_faces=1,
        )
        self.assertTrue(result.ranked)
        self.assertTrue(result.filtered)
        self.assertEqual(len(result.filtered), len(result.ranked)) # no filtering

        # px4
        (stream, ranked_edges) = targeting.px4_crawl(self.token)
        self.assertTrue(stream)

        self.assertEqual(models.dynamo.PostTopics.items.count(), 0)

        filtering_result = targeting.px4_filter(
            stream,
            ranked_edges,
            fbid=self.token.fbid,
            campaign_id=self.campaign.pk,
            content_id=self.content.pk,
            visit_id=self.visit.pk,
            num_faces=1,
        )
        result = targeting.px4_rank(filtering_result)

        self.assertTrue(result.ranked)
        self.assertTrue(result.filtered)
        self.assertTrue(classifier_mock.called)

        self.assertGreater(models.dynamo.PostTopics.items.count(), 0)

        self.assertLess(len(result.filtered), len(result.ranked))
        mismatch = [user for user in result.filtered.secondaries
                    if user.topics['Weather'] < 0.1]
        self.assertFalse(mismatch)

    @patch_facebook(min_friends=20, max_friends=30)
    @patch('targetshare.models.dynamo.post_topics.classify', side_effect=classify_fake)
    def test_px4_choiceset_filter(self, classifier_mock):
        # Configure null global filter:
        self.campaign.campaignglobalfilters.create(filter=self.default_filter, rand_cdf=1)

        # Configure choiceset:
        topics_filter = self.client.filters.create()
        topics_filter.filterfeatures.create(
            feature_type=models.relational.FilterFeatureType.objects.get_topics(),
            feature='topics[Weather]',
            operator=models.FilterFeature.Operator.MIN,
            value=0.1,
        )
        choice_set = self.client.choicesets.create()
        choice_set.choicesetfilters.create(filter=topics_filter)
        self.campaign.campaignchoicesets.create(choice_set=choice_set, rand_cdf=1)

        # px3
        ranked_edges = targeting.px3_crawl(self.token)
        result = targeting.perform_filtering(
            ranked_edges,
            fbid=self.token.fbid,
            campaign_id=self.campaign.pk,
            content_id=self.content.pk,
            visit_id=self.visit.pk,
            num_faces=1,
        )
        self.assertTrue(result.ranked)
        self.assertTrue(result.filtered)
        self.assertEqual(len(result.filtered), len(result.ranked)) # no filtering

        # px4
        (stream, ranked_edges) = targeting.px4_crawl(self.token)
        self.assertTrue(stream)

        self.assertEqual(models.dynamo.PostTopics.items.count(), 0)

        filtering_result = targeting.px4_filter(
            stream,
            ranked_edges,
            fbid=self.token.fbid,
            campaign_id=self.campaign.pk,
            content_id=self.content.pk,
            visit_id=self.visit.pk,
            num_faces=1,
        )
        result = targeting.px4_rank(filtering_result)

        self.assertTrue(result.ranked)
        self.assertTrue(result.filtered)
        self.assertTrue(classifier_mock.called)

        self.assertGreater(models.dynamo.PostTopics.items.count(), 0)

        self.assertLess(len(result.filtered), len(result.ranked))
        mismatch = [user for user in result.filtered.secondaries
                    if user.topics['Weather'] < 0.1]
        self.assertFalse(mismatch)
