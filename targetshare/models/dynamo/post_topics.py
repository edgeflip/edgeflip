from targetshare.classifier import classify

from faraday import Item, HashKeyField, NUMBER, STRING


class PostTopics(Item):

    postid = HashKeyField(data_type=STRING)

    class Meta(object):
        allow_undeclared_fields = True
        undeclared_data_type = NUMBER

    @classmethod
    def classify(cls, postid, text, *topics):
        """Classify the given `text` using the quick-and-dirty pseudo-classifier
        and instantiate a new PostTopics instance.

        """
        classifications = classify(text, *topics)
        return cls(postid=postid, **classifications)
