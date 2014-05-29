from StringIO import StringIO

from django.conf import settings
from django.utils.unittest import TestCase
from mock import patch

from targetshare import classifier
from targetshare.utils import atan_norm


DATA = '''\
Education,Education,1,0
Education,teacher,0.9,0
Education,training,0.6,0
Education,student,0.6,0
Education,students,0.6,0
Education,teachers,0.9,0
Education,courses,0.9,0
Education,classroom,0.9,0
Education,lesson plan,0.9,0
Education,lesson plans,0.9,0
Education,curriculum,0.9,0
Education,educator,0.9,0
Education,educate,0.9,0
Education,college,0.9,0
Education,school,0.9,0
Education,university,0.9,0
Education,kindergarten,0.9,0
Education,pre school,0.9,0
Education,teaching,0.6,0
Education,home schooling,0.9,0
Healthcare,health care,1,0
Healthcare,medicine,1,0
Healthcare,medical,1,0
Healthcare,health,1,0
Healthcare,medicaid,1,0
Healthcare,medicare,1,0
Healthcare,cancer,0.9,0
'''

SHORT_DATA = '\n'.join(DATA.splitlines()[16:21]) # no trailling \n

CHUNK_SIZE = 15
CHUNKED_DATA = [DATA[pos:(pos + CHUNK_SIZE)] for pos in xrange(0, len(DATA), CHUNK_SIZE)]


def s3_data_patch(chunks):
    return patch('boto.connect_s3', **{'return_value.get_bucket.return_value.get_key.return_value': chunks})


class TestS3XReadLines(TestCase):

    @s3_data_patch([SHORT_DATA])
    @patch.multiple(settings, AWS_ACCESS_KEY_ID=None)
    def test_no_creds(self, _s3_mock):
        with self.assertRaises(StopIteration):
            next(classifier.s3_key_xreadlines())

    @s3_data_patch([SHORT_DATA])
    @patch.multiple(settings, AWS_ACCESS_KEY_ID='user', AWS_SECRET_ACCESS_KEY='secret')
    def test_short_content(self, _s3_mock):
        self.assertEqual(list(classifier.s3_key_xreadlines()), StringIO(SHORT_DATA).readlines())

    @s3_data_patch([DATA])
    @patch.multiple(settings, AWS_ACCESS_KEY_ID='user', AWS_SECRET_ACCESS_KEY='secret')
    def test_full_content(self, _s3_mock):
        self.assertEqual(list(classifier.s3_key_xreadlines()), StringIO(DATA).readlines())

    @s3_data_patch(CHUNKED_DATA)
    @patch.multiple(settings, AWS_ACCESS_KEY_ID='user', AWS_SECRET_ACCESS_KEY='secret')
    def test_chunked_content(self, _s3_mock):
        self.assertEqual(list(classifier.s3_key_xreadlines()), StringIO(DATA).readlines())

    @patch.multiple(settings, AWS_ACCESS_KEY_ID='user', AWS_SECRET_ACCESS_KEY='secret')
    def test_chunked_content_no_trailer(self):
        chunks = CHUNKED_DATA[:-1]
        stripped = CHUNKED_DATA[-1].strip()
        with s3_data_patch(chunks + [stripped]):
            self.assertEqual(''.join(classifier.s3_key_xreadlines()), DATA.strip())


@s3_data_patch(CHUNKED_DATA)
@patch.multiple(settings, AWS_ACCESS_KEY_ID='user', AWS_SECRET_ACCESS_KEY='secret')
class TestSimpleWeights(TestCase):

    def test_load(self, _s3_mock):
        weights = classifier.SimpleWeights.load(classifier.s3_key_xreadlines())
        self.assertEqual(len(weights), 2)

        topic_data = [line.split(',') for line in DATA.splitlines()]
        for (topic, info) in weights.iteritems():
            topic_lines = [
                (phrase, float(weight), bool(int(skip)))
                for (topic1, phrase, weight, skip) in topic_data
                if topic1 == topic
            ]
            topic_info = [topic_info[:3] for topic_info in info]
            self.assertEqual(topic_info, topic_lines)

    def test_iter_topic(self, _s3_mock):
        weights = classifier.SimpleWeights.load(classifier.s3_key_xreadlines())
        self.assertItemsEqual(
            weights.iter_topics("About 75% of New York City School students qualify "
                                "for free or reduced-price lunch.", 'Healthcare'),
            [('Healthcare', 0)]
        )

    def test_iter_topics(self, _s3_mock):
        weights = classifier.SimpleWeights.load(classifier.s3_key_xreadlines())
        self.assertItemsEqual(
            weights.iter_topics("About 75% of New York City School students qualify "
                                "for free or reduced-price lunch."),
            [('Healthcare', 0),
             ('Education', 0.6 + 0.9)] # students, school
        )

    def test_iter_topic_undefined(self, _s3_mock):
        weights = classifier.SimpleWeights.load(classifier.s3_key_xreadlines())
        self.assertItemsEqual(
            weights.iter_topics("About 75% of New York City School students qualify "
                                "for free or reduced-price lunch.", 'Sports'),
            [('Sports', 0)]
        )

    def test_iter_topic_phrase_linking(self, _s3_mock):
        weights = classifier.SimpleWeights.load(classifier.s3_key_xreadlines())
        self.assertItemsEqual(
            weights.iter_topics(
                "Home-schooling parents and teachers can include our fun and free "
                "preschool activities and worksheets in their lesson plans",
                'Education'
            ),
            [('Education', 0.9 + 0.9 + 0.9 + 0.9)] # home schooling, teachers, pre school, lesson plans
        )

    def test_classify(self, _s3_mock):
        weights = classifier.SimpleWeights.load(classifier.s3_key_xreadlines())
        self.assertEqual(
            weights.classify("About 75% of New York City School students qualify "
                             "for free or reduced-price lunch."),
            {'Healthcare': 0,
             'Education': atan_norm(0.6 + 0.9)} # students, school
        )
