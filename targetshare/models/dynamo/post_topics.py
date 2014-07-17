import decimal

from boto.dynamodb.types import DYNAMODB_CONTEXT
from faraday import Item, ItemManager, HashKeyField, RangeKeyField, NUMBER, STRING

from targetshare.classifier import classify


BG_CLASSIFIER = 'background'
QD_CLASSIFIER = 'quick-dirty'

CLASSIFIERS = (BG_CLASSIFIER, QD_CLASSIFIER)

CLASSIFY_CONTEXT = DYNAMODB_CONTEXT.copy()
CLASSIFY_CONTEXT.prec = 3
CLASSIFY_CONTEXT.traps.update({
    decimal.Inexact: False,
    decimal.Rounded: False,
})


class PostTopicsManager(ItemManager):

    def batch_get_best(self, postids, classifiers=CLASSIFIERS):
        """Retrieve the set of PostTopics for the given iterable of `postids`,
        preferring one classifier over another, as dictated by `classifiers`.

        PostTopics for the given post IDs are batch-gotten, for each classifier
        type, until all requested posts have been retrieved, or no classifiers remain.

        A length-2 tuple of `(post_topics_list, missing_key_set)` is returned.

        """
        missing_keys = set(postids)
        all_items = []

        for classifier in classifiers:
            items = self.batch_get([{'postid': postid, 'classifier': classifier}
                                    for postid in missing_keys])
            all_items.extend(items)
            missing_keys.difference_update(item.postid for item in items)
            if not missing_keys:
                break

        return (all_items, missing_keys)


class PostTopics(Item):

    BG_CLASSIFIER = BG_CLASSIFIER
    QD_CLASSIFIER = QD_CLASSIFIER

    CLASSIFIERS = CLASSIFIERS

    postid = HashKeyField(data_type=STRING)
    classifier = RangeKeyField(data_type=STRING)

    items = PostTopicsManager()

    class Meta(object):
        allow_undeclared_fields = True
        undeclared_data_type = NUMBER

    @classmethod
    def classify(cls, postid, text, *topics):
        """Classify the given `text` using the quick-and-dirty classifier and
        instantiate a new PostTopics instance.

        """
        classifications = classify(text, *topics)
        # DDB/Decimals are exact; eagerly convert to Decimal with
        # appropriate Context to avoid error:
        prepared = {topic: CLASSIFY_CONTEXT.create_decimal(score)
                    for (topic, score) in classifications.iteritems()}
        return cls(postid=postid, classifier=cls.QD_CLASSIFIER, **prepared)
